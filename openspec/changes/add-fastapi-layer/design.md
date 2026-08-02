## Context

See proposal.md — Why. The relevant current state:

- `src/tienda/domain/` holds `Product` (frozen-ish dataclass validating `price >= 0` in `__post_init__`), `CartLine` (dataclass with `subtotal`), `Cart` (dict of `product_id → CartLine`, with `add`/`remove`/`clear`/`total`, raising `ProductNotFound` on an unknown id), and the `CartRepository` protocol (`get`/`save`).
- `src/tienda/infrastructure/in_memory_cart_repository.py` holds one process-wide `Cart` and returns the same mutable instance from `get()`.
- `src/tienda/api/main.py` has `GET /cart` and `POST /cart/items`. `POST` builds its response by calling the `get_cart` handler function directly, depends on the concrete repository type, and never calls `save`.
- Tests run under pytest with `TestClient`; `app.dependency_overrides` already swaps in a fresh repository per test.

Constraint: the domain layer is the tested core and is not to be edited by this change — the API adapts to it, not the reverse.

## Goals / Non-Goals

**Goals:**

- One HTTP route per domain operation, with the domain reachable only through the repository protocol.
- Cart → response mapping written once, so route handlers stay thin and never call each other.
- Domain exceptions translated to HTTP centrally, so a new route inherits the mapping for free.
- The API layer stays substitutable: swapping `InMemoryCartRepository` for a persistent one requires no route changes.

**Non-Goals:**

- An application/use-case layer between routes and domain. The operations are single domain calls; a service layer here would be pass-through indirection.
- Async handlers. Nothing in the stack does I/O.
- Versioned paths, pagination, ETags, or idempotency keys.

## Decisions

### Exception handler over per-route try/except

Register `ProductNotFound` with `@app.exception_handler` and return a 404 `JSONResponse` with a `detail` field. Alternative considered: `try/except` in each handler raising `HTTPException`. Rejected — it repeats the mapping at every call site and drifts as routes are added. The handler keeps route bodies to "call the domain, save, map"; adding a domain exception later means one new handler, not N new `except` clauses.

The body shape stays `{"detail": "..."}` to match what FastAPI's own `HTTPException` and validation errors already emit, so clients see one error format.

### The domain owns the price invariant; the API only translates its failure

`ProductIn` keeps `price: int` and adds **no** `ge=0` constraint. A negative price flows through the schema, reaches `Product.__post_init__`, and raises `ValueError`; a `ValueError` exception handler registered on `app` returns 422 with the exception message as `detail`. Pydantic still rejects a missing field or a non-integer price at the schema layer, since those are wire-format concerns rather than domain rules.

Alternative considered and rejected: `Field(ge=0)` on `ProductIn.price`, rejecting the value before a `Product` exists. It is faster and self-documenting in OpenAPI, but it restates a rule the domain already enforces — two places to change when the rule changes, and nothing forces them to stay in step. Single source of truth wins: the invariant lives in `Product`, and the API layer's job is to translate a domain refusal into the right status code, not to re-derive it.

Two consequences of that, both accepted:

- **422 bodies are not uniform.** A missing or non-integer field yields Pydantic's list-shaped `detail`; a negative price yields a plain string `detail` from the domain message. Both are 422, which is all the spec requires — no scenario pins the 422 body shape.
- **OpenAPI no longer advertises the constraint.** `price` is documented as a plain integer, and clients discover the rule by being rejected. The alternative bought this at the cost of the duplication above.

### Where the `ValueError` handler is registered, and how its breadth is contained

The handler is registered for `ValueError` on the app, alongside the `ProductNotFound` handler, so the two domain failures are translated in the same place and a new route inherits both.

`ValueError` is broader than the invariant it is standing in for: an unrelated `ValueError` raised by a bug inside a route would be reported to the client as 422 rather than 500. Containment, in order of preference:

1. Route handlers stay thin — call the domain, save, map — so the only `ValueError`-raising call reachable from a route is `Product(...)` construction in the add route.
2. If that ever stops holding, the domain can introduce `InvalidProduct(ValueError)` and raise it from `__post_init__`; the handler narrows to that type and the invariant still lives in exactly one place. This costs no change to the HTTP contract, so it is deliberately deferred rather than done now — it would be a domain edit, and this change does not touch the domain.

### Mutate-then-save, even though the in-memory repository aliases

Handlers do `cart = repo.get()` → mutate → `repo.save(cart)`. With `InMemoryCartRepository` the `save` is a no-op in effect, since `get()` hands back the live object. It is written anyway so the routes express the contract the `CartRepository` protocol actually promises. A repository that deserializes a fresh `Cart` per `get()` would otherwise silently drop every mutation, and the bug would surface as "the API works until you swap the repository".

### A single `cart_to_out` mapper in `api/mappers.py`

One function `Cart → CartOut`, used by all four routes. Alternative considered: a `CartOut.from_domain` classmethod. Rejected to keep `schemas.py` free of domain imports — the schemas describe the wire format, and the direction of knowledge stays one-way (mappers know both sides; schemas know neither).

### Dependency typed as the `CartRepository` protocol

`get_cart_repository()` is annotated `-> CartRepository`, and handlers take `repo: CartRepository = Depends(...)`. The concrete `InMemoryCartRepository` is named only at the module-level singleton. FastAPI does not introspect the return type for injection, so a `Protocol` annotation is safe here and documents the seam. Existing tests override the dependency by callable identity, which is unaffected.

### Route shapes

| Operation | Route | Status | Body |
|---|---|---|---|
| Read | `GET /cart` | 200 | `CartOut` |
| Add | `POST /cart/items` | 201 | `CartOut` |
| Remove one unit | `DELETE /cart/items/{product_id}` | 200 | `CartOut` |
| Empty | `DELETE /cart` | 200 | `CartOut` |

Every mutating route returns the full cart so a client never needs a follow-up `GET`. `DELETE` returns 200 with a body rather than 204, since 204 forbids one.

Remove is addressed by `product_id` in the path and takes no body. `Cart.remove` accepts a `Product`, so the handler reads the existing line to recover the real product; if the id is absent, it raises `ProductNotFound` — the same error the domain would raise, mapped to 404 by the handler above. This keeps the API from having to invent a `Product` with placeholder name and price just to satisfy the domain signature.

## Risks / Trade-offs

- **Mapping `ValueError` to 422 is broader than the invariant it stands for: an internal bug raising `ValueError` inside a route would be reported to the client as a validation error instead of a 500.** → Thin route handlers keep `Product(...)` as the only reachable raiser; the `InvalidProduct(ValueError)` narrowing above is the escape hatch if that stops holding. Accepted as the price of a single source of truth for the invariant.
- **The domain's exception message becomes client-facing copy the moment it is used as `detail`.** → It is already user-safe (it names the rule and the offending value and leaks nothing internal). Worth knowing that `Product` currently reads `"Product Price must be zero o higher"` — a typo that is now visible to API clients. Fixing it is a one-word domain edit that this change deliberately does not make; it belongs to whoever next touches the domain.
- **The price rule is invisible in the generated OpenAPI, so clients learn it only by being rejected.** → Accepted per the decision above; a spec scenario pins the 422, and the endpoint description can name the rule in prose without re-encoding it as a schema constraint.
- **`DELETE /cart/items/{product_id}` decrements by one rather than removing the whole line, which can surprise clients reading it as "delete this resource".** → It matches `Cart.remove` and is pinned by two spec scenarios; a future `?all=true` or `PATCH` on quantity can be added without breaking it.
- **The repository singleton is process-wide, so all clients share one cart.** → Out of scope per the proposal; the protocol seam is where a per-session repository would later be introduced, and no route needs to change for it.
- **Writing `repo.save(cart)` against an aliasing repository means the tests cannot detect a forgotten `save`.** → Accepted. The cost is one line per handler; the alternative is routes that encode an implementation detail of one repository.

## Migration Plan

Additive. `GET /cart` and `POST /cart/items` keep their paths, request payloads, and status codes, so existing clients and `tests/test_api.py` continue to pass unchanged. Rollback is reverting the commit; no data or schema migration exists.
