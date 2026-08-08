## 1. Product & catalog domain

- [x] 1.1 Add `stock: int = 0` to `Product` (`src/tienda/domain/product.py`); confirm existing `test_product.py` and all `Product(...)` call sites still pass unchanged.
- [x] 1.2 Add `tests/test_product.py` cases for `stock` defaulting to 0 and being settable.
- [x] 1.3 Add `tienda.domain.exceptions.InsufficientStock` alongside `ProductNotFound`.
- [x] 1.4 Write `tests/test_catalog.py`: listing products, validating an existing/non-existent product id, committing a quantity decrements stock, committing more than available stock raises `InsufficientStock` and leaves stock unchanged.
- [x] 1.5 Add `ProductCatalog` Protocol (e.g. `src/tienda/domain/catalog.py`) with `list_products()`, `get(product_id)`, and `commit(product_id, quantity)`.
- [x] 1.6 Implement `InMemoryProductCatalog` (`src/tienda/infrastructure/in_memory_product_catalog.py`) satisfying `tests/test_catalog.py`, seeded with a fixed list of sample products/stock.

## 2. Order extraction

- [x] 2.1 Define `ExtractedLine` (source_text, quantity, product_id: str | None) and the `OrderExtractor` Protocol (`extract(text, products) -> list[ExtractedLine]`), e.g. in `src/tienda/domain/extraction.py`.
- [x] 2.2 Implement `FakeOrderExtractor` (test double) with deterministic, caller-controlled text-to-line mapping; add `tests/test_fake_order_extractor.py` covering: known-product text, no-match text, ambiguous text.
- [x] 2.3 Implement `AnthropicOrderExtractor` using Anthropic tool-use, given the current catalog as context, constrained to return only known product ids or a no-match sentinel per line. Add `anthropic` to `pyproject.toml`.
- [x] 2.4 Add a focused test (recorded fixture or mocked Anthropic client response, not a live API call) verifying `AnthropicOrderExtractor` maps a tool-use response into `ExtractedLine`s correctly.

## 3. From-text suggestion flow

- [x] 3.1 Write tests for the application-level suggestion logic: given extracted lines and a catalog, produce `SuggestedLine`s where each is `pending` (matched, catalog-authoritative name/price) or `unmatched` (no confident single match), and confirm the catalog/cart are untouched.
- [x] 3.2 Implement the `SuggestedLine` type and the function/service that turns `(text, OrderExtractor, ProductCatalog)` into a list of `SuggestedLine`s, re-validating every extracted `product_id` against the catalog before returning it.
- [x] 3.3 Add `TextOrderIn` / `SuggestedLineOut` / `SuggestedOrderOut` API schemas (`src/tienda/api/schemas.py`) and a mapper to serialize `SuggestedLine`s, matching the `pending`/`unmatched` shape from `specs/cart-from-text/spec.md`.
- [x] 3.4 Add `POST /cart/from-text` to `src/tienda/api/main.py`, wired to `OrderExtractor`/`ProductCatalog` dependencies (default real implementations, overridable like `get_cart_repository`).
- [x] 3.5 Add `tests/test_api.py` cases for `/cart/from-text` using the fake extractor: known products → pending lines; unknown text → unmatched lines; response never mutates `GET /cart`.

## 4. Confirm flow

- [x] 4.1 Write tests for the confirm application logic: valid lines become confirmed `CartLine`s in the cart and decrement catalog stock; any invalid line (unknown product or insufficient stock) rejects the whole batch and leaves cart/stock unchanged.
- [x] 4.2 Implement the confirm service/function operating on `(lines, Cart, ProductCatalog)`, validating all lines before committing any.
- [x] 4.3 Add `ConfirmLineIn` / `ConfirmOrderIn` API schemas and wire `POST /cart/confirm` in `main.py`, returning the updated `CartOut` on success.
- [x] 4.4 Add exception handlers (or extend existing ones) mapping `InsufficientStock` to 409 and an unknown `product_id` in a confirm request to 404, per the existing `ProductNotFound` handler pattern.
- [x] 4.5 Add `tests/test_api.py` cases for `/cart/confirm`: successful confirm updates `GET /cart` and reduces catalog stock; insufficient-stock line rejects the whole request with cart unchanged; unknown product id rejects with 404.

## 5. Wiring & cleanup

- [x] 5.1 Wire `get_product_catalog()` and `get_order_extractor()` dependencies in `main.py`, mirroring `get_cart_repository()`, defaulting to `InMemoryProductCatalog` and `AnthropicOrderExtractor`.
- [x] 5.2 Run the full test suite (`pytest`) and confirm all pre-existing tests pass unmodified alongside the new ones.
- [x] 5.3 Run `openspec validate add-cart-from-text --strict` and fix any reported issues.
