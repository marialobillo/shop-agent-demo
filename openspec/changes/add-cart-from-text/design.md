## Context

Today `Product` is a plain `(product_id, name, price)` value with no stock and no catalog — products only exist as whatever the caller passes to `POST /cart/items`. `Cart`/`CartLine` only ever hold confirmed lines, there's a single global in-memory cart (no sessions/users), and `CartRepository` is the only Protocol/fake pattern in the codebase (`InMemoryCartRepository`, overridden in tests via `app.dependency_overrides`). See `proposal.md` for motivation and `specs/product-catalog` / `specs/cart-from-text` for the behavior this must satisfy.

## Goals / Non-Goals

**Goals:**
- Keep the existing `Cart`/`CartLine`/`GET /cart`/`POST /cart/items` behavior and API responses byte-for-byte unchanged (existing tests must pass untouched).
- Keep `OrderExtractor` and `ProductCatalog` as small Protocols with a real and a fake/in-memory implementation, following the existing `CartRepository` pattern.
- Make validation-before-display and no-reservation-until-confirm structurally obvious, not just documented.

**Non-Goals:**
- Persisting pending suggestions server-side, sessions, or multi-user carts (see proposal Non-Goals: no auth).
- Structured product variant modeling (separate color/size fields); text matching is handled by the LLM against product names/descriptions.
- Any real product-admin/catalog-management capability — the catalog is seeded with fixed data for this change.

## Decisions

### 1. Suggested lines are not persisted; `/cart/confirm` is stateless
`POST /cart/from-text` does not store anything server-side. It returns suggested lines to the caller; `POST /cart/confirm` takes the lines to confirm (`product_id` + `quantity`) directly in its request body — effectively the caller round-trips the `pending` lines it wants to accept.
**Alternative considered:** a server-side pending-order store keyed by an id returned from `from-text`. Rejected for now: without a user/session concept (explicit non-goal) there's no natural owner for that state, and it adds a second piece of mutable server state for no behavioral gain at this scale. Revisit once carts are tied to a logged-in user.

### 2. Domain `CartLine` is untouched; pending suggestions are a separate type
Rather than adding a `status` field to the existing `CartLine` dataclass, introduce a distinct application-layer type (e.g. `SuggestedLine`: `source_text`, `quantity`, and optionally a matched `product_id`/`name`/`price`) that is never stored in `Cart`. The API layer serializes these with `status: "pending"` / `"unmatched"` to match the proposal's described response shape.
**Alternative considered:** add `status: Literal["pending", "confirmed"]` to `CartLine` itself. Rejected: `Cart.lines` would then need to either filter by status everywhere (total, add, remove) or risk pending lines leaking into totals/removal — the existing `Cart` tests assume every line in `cart.lines` is real and confirmed. Keeping suggestions out of `Cart` entirely avoids that class of bug.

### 3. `Product` gains a `stock: int = 0` field with a default
Existing tests construct `Product(product_id, name, price)` positionally in ~20 places. Adding `stock` as a fourth field with a default of `0` keeps every existing call site valid; only catalog-seeded products set it explicitly.

### 4. Extraction returns catalog-scoped candidates; validation happens twice, cheaply
`OrderExtractor.extract(text, products)` is given the current catalog's products (id, name, price) as context and returns `ExtractedLine(source_text, quantity, product_id: str | None)` — `product_id` is either one of the given catalog ids or `None` if the extractor found no confident match. The Anthropic implementation enforces this at the tool-use layer (the `product_id` argument is constrained to an enum of current catalog ids, or a `null`/no-match sentinel), so hallucinated ids are structurally unlikely — but the `/cart/from-text` handler still re-looks-up every returned `product_id` against `ProductCatalog` before building the response, per the "validated before shown" requirement. This keeps the extractor swappable (fake vs real) without weakening the guarantee, since the fake could misbehave too.
**Alternative considered:** trust the LLM's structured output as already-valid. Rejected — it violates the explicit requirement that suggestions are checked against the real catalog before being shown, and a fake extractor used in tests has no such guarantee either.

### 5. Ambiguous matches are treated as unmatched
If extraction (or the validation re-lookup) can't resolve a candidate to exactly one catalog product, the line is returned with `status: "unmatched"` alongside the original `source_text`/`quantity`, with no `product_id`/`name`/`price`. No separate "ambiguous" status — from the customer's point of view both cases mean "we couldn't confidently pick one product for this."

### 6. `/cart/confirm` is all-or-nothing per request
Confirming validates every requested line (product exists, quantity ≤ current stock) before committing any of them. If any line fails, the whole request is rejected (409 for insufficient stock, 404 for an unknown `product_id`, mirroring the existing `ProductNotFound` handler pattern) and the cart is left completely unchanged.
**Alternative considered:** best-effort partial commit (confirm what's valid, report what isn't). Rejected for this change — partial success responses are more complex to model and test, and at kata scale a customer can simply resubmit a trimmed request.

### 7. `ProductCatalog` implementation and seed data
An `InMemoryProductCatalog` (mirroring `InMemoryCartRepository`) holds a fixed, hardcoded list of seed products with stock, constructed once in `main.py` and exposed via a `get_product_catalog()` dependency, overridable in tests exactly like `get_cart_repository()`.

### 8. `OrderExtractor` implementations
- `AnthropicOrderExtractor`: uses the `anthropic` SDK's tool-use to call a single tool (e.g. `extract_order_lines`) whose input schema captures `[{source_text, quantity, product_id}]`, with the current catalog serialized into the prompt/tool schema so the model can only reference real ids.
- `FakeOrderExtractor`: deterministic, constructed with a caller-supplied mapping or simple substring/keyword matching against the given products — used in unit and API tests so they don't depend on network access or nondeterministic output.

Both live behind `OrderExtractor` and are wired the same way `CartRepository` is: a `get_order_extractor()` FastAPI dependency, defaulting to the real one, overridden with the fake in tests.

## Risks / Trade-offs

- **[Risk]** LLM extraction is inherently non-deterministic and can misparse quantities/products → **Mitigation**: mandatory catalog validation before display (Decision 4) means the worst case is an item marked `unmatched`, never a wrong or fabricated product shown as `pending`.
- **[Risk]** No stock reservation means two customers can be shown the same available stock as suggestions and race at confirm → **Mitigation**: accepted per proposal's explicit non-goal; `/cart/confirm` re-validates stock at commit time (Decision 6) so the loser of the race gets a clear insufficient-stock rejection instead of oversold stock.
- **[Risk]** Stateless confirm requires the client to resend full line data, which is slightly more payload than an opaque suggestion id → **Mitigation**: acceptable trade-off for avoiding server-side session state (Decision 1); revisit once carts are user-linked.
- **[Risk]** `anthropic` SDK calls add latency and an external dependency to `/cart/from-text` → **Mitigation**: isolated behind `OrderExtractor`, so tests and any future fallback path never depend on it.

## Migration Plan

- No data migration: this is additive (new fields with defaults, new endpoints, new dependency).
- Add `anthropic` to `pyproject.toml` dependencies; the Anthropic API key is read from environment configuration for the real `OrderExtractor` implementation.
- Roll out as a normal deploy; rollback is removing the new routes/dependency wiring since nothing existing is modified in place.

## Open Questions

- Exact seed data for the in-memory catalog (which products/prices/stock) — can be filled in during implementation without affecting the spec or approach.
