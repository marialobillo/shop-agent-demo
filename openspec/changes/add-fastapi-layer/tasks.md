## 1. Package scaffolding

- [x] 1.1 Add empty `src/tienda/api/__init__.py` so `api` is a regular package like `domain` and `infrastructure`
- [x] 1.2 Run `pytest` and confirm the existing suite still passes as a baseline

## 2. Schemas and mapping

- [x] 2.1 Leave `ProductIn.price` as a plain `int` in `src/tienda/api/schemas.py` — do **not** add `Field(ge=0)`; the `price >= 0` rule stays owned by `Product.__post_init__` and is translated in task 4.2
- [x] 2.2 Add an `ErrorOut` schema with a `detail: str` field, for documenting 404 responses in OpenAPI
- [x] 2.3 Create `src/tienda/api/mappers.py` with `cart_to_out(cart: Cart) -> CartOut` building `CartLineOut` per line plus the total
- [x] 2.4 Rewrite `GET /cart` and `POST /cart/items` to use `cart_to_out`; `POST` must stop calling the `get_cart` handler function to build its response

## 3. Repository seam

- [x] 3.1 Annotate `get_cart_repository()` as returning `CartRepository` and type every handler's `repo` parameter as `CartRepository`
- [x] 3.2 Make `POST /cart/items` call `repo.save(cart)` after mutating, per the mutate-then-save decision in design.md

## 4. Error handling

- [x] 4.1 Register a `ProductNotFound` exception handler on `app` returning 404 with `{"detail": "..."}` naming the product identifier
- [x] 4.2 Register a `ValueError` exception handler on `app` returning 422 with the exception message as `detail`, so `Product`'s own `price >= 0` check is what rejects a negative price
- [x] 4.3 Keep route handlers thin (call domain → save → map) so `Product(...)` stays the only `ValueError`-raising call reachable from a route, per the containment note in design.md
- [x] 4.4 Add a test that removing an absent product returns 404 (not 500) with a JSON `detail` field — expected to fail until section 5 adds the route

## 5. Remove endpoint

- [x] 5.1 Write failing tests for `DELETE /cart/items/{product_id}`: quantity two decrements to one, quantity one drops the line, absent id returns 404 and leaves the cart unchanged
- [x] 5.2 Implement `DELETE /cart/items/{product_id}` returning 200 and the full cart; look up the existing line to recover the real `Product` before calling `Cart.remove`, and raise `ProductNotFound(product_id)` when the id is absent
- [x] 5.3 Call `repo.save(cart)` after the mutation and confirm the section 5.1 and 4.4 tests pass

## 6. Clear endpoint

- [x] 6.1 Write failing tests for `DELETE /cart`: emptying a cart with two products returns `{"lines": [], "total": 0}`, a later `GET /cart` agrees, and emptying an already empty cart also returns 200
- [x] 6.2 Implement `DELETE /cart` calling `Cart.clear`, saving, and returning 200 with the emptied cart; confirm the tests pass

## 7. Validation and remaining coverage

- [x] 7.1 Add tests for invalid add payloads: negative price returns 422 via the domain `ValueError` handler, a payload missing `name` returns 422 via Pydantic, and the cart is unchanged in both cases — assert only the status and that the cart is untouched, since the two paths produce different `detail` shapes
- [x] 7.2 Add a test that price 0 is accepted with 201 and a subtotal of 0
- [x] 7.3 Add tests covering the read scenarios not yet exercised: a cart with two distinct products returns one line each with `total` as the sum of subtotals
- [x] 7.4 Remove the duplicated `client = TestClient(app)` and the redundant `clean_cart` fixture in `tests/test_api.py` (it shadows `fresh_repository` and calls `app.dependency_overrides.clear` without invoking it)

## 8. Verification

- [x] 8.1 Run the full `pytest` suite and confirm every test passes
- [x] 8.2 Start the app with `uvicorn tienda.api.main:app` and check `/docs` lists all four routes with their status codes
- [x] 8.3 Run `openspec validate add-fastapi-layer --strict` and confirm every spec scenario has a corresponding test
