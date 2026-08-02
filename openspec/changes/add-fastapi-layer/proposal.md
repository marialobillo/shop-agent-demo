## Why

The domain layer (`Cart`, `CartLine`, `Product`, `CartRepository`) is complete and tested, but only two of its four operations are reachable over HTTP: `GET /cart` and `POST /cart/items`. `Cart.remove` and `Cart.clear` have no endpoint, domain errors leak as 500s instead of proper HTTP status codes, and the endpoint handlers build response models inline — duplicating mapping logic that will multiply with every new route.

## What Changes

- Add `DELETE /cart/items/{product_id}` to decrement (or drop) a line, exposing `Cart.remove`.
- Add `DELETE /cart` to empty the cart, exposing `Cart.clear`.
- Map `ProductNotFound` to HTTP 404 with a structured error body, via a FastAPI exception handler rather than per-endpoint try/except.
- Map the `ValueError` that `Product` already raises for `price >= 0` to HTTP 422 instead of letting it surface as a 500. The request schema does **not** restate the rule: the domain stays the single source of truth for the invariant, and the API only translates its failure.
- Extract Cart → `CartOut` mapping into a single reusable function; endpoints stop calling each other to build responses.
- Persist through the repository: handlers call `repo.save(cart)` after mutating, so the API no longer depends on `InMemoryCartRepository` returning a live mutable reference.
- Type endpoint dependencies against the `CartRepository` protocol instead of the concrete `InMemoryCartRepository`.
- Add `src/tienda/api/__init__.py` so `api` is a regular package like `domain` and `infrastructure`.
- Extend `tests/test_api.py` to cover every endpoint and error path.

Non-goals: authentication, persistence beyond in-memory, multi-user carts, product catalog endpoints.

## Capabilities

### New Capabilities
- `cart-api`: HTTP interface over the existing cart domain — read the cart, add a product, remove a product, empty the cart, and the status codes and error bodies each produces.

### Modified Capabilities
<!-- None: the domain's behavior is unchanged; this change only exposes it over HTTP. -->

## Impact

- **Code**: `src/tienda/api/main.py` (rewritten routes + exception handlers), `src/tienda/api/schemas.py` (error schema only — no new field constraints), new `src/tienda/api/__init__.py`, new `src/tienda/api/mappers.py`.
- **Domain**: unchanged. No edits to `src/tienda/domain/`.
- **Infrastructure**: unchanged; the API depends on the `CartRepository` protocol.
- **Tests**: `tests/test_api.py` extended; `tests/test_cart.py` and `tests/test_product.py` untouched.
- **Dependencies**: none added — `fastapi`, `uvicorn`, `httpx`, `pytest` already declared.
- **API consumers**: additive. `GET /cart` and `POST /cart/items` keep their paths, payloads, and status codes.
