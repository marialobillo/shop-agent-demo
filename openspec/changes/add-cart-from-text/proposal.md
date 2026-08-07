## Why

Customers currently must add items to the cart one product at a time through `POST /cart/items`, which means they need to already know exact product ids. Letting a customer type a free-text order ("2 blue shirts size M and a pair of jeans") and get back matched cart suggestions removes that friction and is a natural fit for an LLM-assisted flow.

## What Changes

- Add `POST /cart/from-text`: accepts free-text input, extracts candidate order lines via an LLM, matches them against the real product catalog, and returns them as suggested `CartLine`s with status `pending`. Lines that cannot be matched to a real product are surfaced as unmatched/rejected rather than silently dropped.
- Add `POST /cart/confirm` (or equivalent): accepts a set of pending lines and turns them into confirmed `CartLine`s in the cart, decrementing stock at this point (not earlier).
- Introduce an `OrderExtractor` Protocol for LLM-based extraction, with two implementations: an Anthropic tool-use–based extractor for production, and a deterministic fake for unit tests.
- Introduce a `ProductCatalog` Protocol that supplies the product context passed to the extractor and is also the source of truth used to validate suggested lines before they are shown to the customer.
- Extend the product/catalog model with a `stock` quantity, decremented only on confirm (no reservation on suggestion).
- Extend `CartLine` (or introduce a related type) with a `pending` / `confirmed` status so suggested and confirmed lines can be represented and distinguished.

## Capabilities

### New Capabilities
- `product-catalog`: a queryable catalog of products (with stock) used as LLM context and as the validation source of truth for suggested lines; also owns stock decrement on confirm.
- `cart-from-text`: free-text extraction into pending suggested cart lines, validation of those suggestions against the real catalog, and a confirm step that turns accepted pending lines into confirmed cart lines.

### Modified Capabilities
(none — no existing specs are affected; `cart`/`product` behavior as exposed today is unchanged, this only adds new endpoints and a pending-line concept alongside it)

## Impact

- New domain concepts: product stock, a pending/confirmed status on cart lines, an `OrderExtractor` Protocol, a `ProductCatalog` Protocol.
- New infrastructure: an Anthropic-tool-use-backed `OrderExtractor` implementation, a deterministic fake `OrderExtractor` for tests, and a catalog implementation (likely in-memory, mirroring `InMemoryCartRepository`).
- New API surface: `POST /cart/from-text`, `POST /cart/confirm`, plus their request/response schemas and mappers.
- New dependency: the `anthropic` Python SDK.
- Existing endpoints (`GET /cart`, `POST /cart/items`, `DELETE /cart`, `DELETE /cart/items/{id}`) and their behavior are unchanged.

## Non-Goals

- User authentication or linking the cart to a logged-in user (future proposal).
- Frontend/UI implementation.
- Stock reservation with TTL — stock is only decremented at confirm/checkout time; no hold is placed while a suggestion is pending.
