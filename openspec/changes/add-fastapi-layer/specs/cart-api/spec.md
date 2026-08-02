## Purpose

Exposes the shopping cart domain over HTTP as a JSON API, so clients can read the cart, add a product, remove a product, and empty the cart without depending on the domain objects directly.

## ADDED Requirements

### Requirement: Read the cart

The API SHALL provide a read operation that returns the current cart as one line per distinct product plus the cart total. Each line SHALL carry the product identifier, name, unit price, quantity, and the line subtotal. The response SHALL use status 200.

#### Scenario: Empty cart

- **WHEN** a client reads the cart and no product has been added
- **THEN** the response status is 200
- **AND** the body is `{"lines": [], "total": 0}`

#### Scenario: Cart with one product

- **WHEN** a client reads a cart holding one unit of product `product_id` named `pair of jeans` priced 3000
- **THEN** the response status is 200
- **AND** the body is `{"lines": [{"product_id": "product_id", "name": "pair of jeans", "price": 3000, "quantity": 1, "subtotal": 3000}], "total": 3000}`

#### Scenario: Cart with several distinct products

- **WHEN** a client reads a cart holding two distinct products
- **THEN** the response contains one line per distinct product
- **AND** `total` equals the sum of the line subtotals

### Requirement: Add a product to the cart

The API SHALL accept a product identifier, name, and price and add one unit of that product to the cart. Adding a product already in the cart SHALL increment that line's quantity rather than create a second line. The response SHALL use status 201 and return the full updated cart in the same shape as the read operation.

#### Scenario: Add a product not yet in the cart

- **WHEN** a client adds product `product_id` named `pair of jeans` priced 3000 to an empty cart
- **THEN** the response status is 201
- **AND** the returned cart has one line for `product_id` with quantity 1 and total 3000

#### Scenario: Add the same product twice

- **WHEN** a client adds the same product a second time
- **THEN** the response status is 201
- **AND** the returned cart still has a single line for that product with quantity 2
- **AND** the total is twice the unit price

#### Scenario: Added product is visible on a later read

- **WHEN** a client adds a product and then reads the cart in a separate request
- **THEN** the read response reflects the added product

### Requirement: Remove a product from the cart

The API SHALL provide a remove operation addressed by product identifier that takes one unit of that product out of the cart. When the line holds more than one unit, the quantity SHALL be decremented by one and the line SHALL remain. When the line holds exactly one unit, the line SHALL be dropped from the cart. The response SHALL use status 200 and return the full updated cart.

#### Scenario: Remove one unit of a product held in quantity two

- **WHEN** a client removes product `product_id` from a cart holding two units of it
- **THEN** the response status is 200
- **AND** the returned cart has a line for `product_id` with quantity 1

#### Scenario: Remove the last unit of a product

- **WHEN** a client removes product `product_id` from a cart holding exactly one unit of it
- **THEN** the response status is 200
- **AND** the returned cart has no line for `product_id`

#### Scenario: Remove a product that is not in the cart

- **WHEN** a client removes a product identifier absent from the cart
- **THEN** the response status is 404
- **AND** the body carries a `detail` message naming the product identifier
- **AND** the cart is left unchanged

### Requirement: Empty the cart

The API SHALL provide an operation that removes every line from the cart in a single call. The response SHALL use status 200 and return the emptied cart. The operation SHALL succeed on an already empty cart.

#### Scenario: Empty a cart holding products

- **WHEN** a client empties a cart holding two distinct products
- **THEN** the response status is 200
- **AND** the body is `{"lines": [], "total": 0}`
- **AND** a later read returns the same empty cart

#### Scenario: Empty an already empty cart

- **WHEN** a client empties a cart that holds no products
- **THEN** the response status is 200
- **AND** the body is `{"lines": [], "total": 0}`

### Requirement: Reject invalid product input

The API SHALL reject an add request whose payload violates the product contract — a missing field, a non-integer price, or a negative price — with status 422 and without modifying the cart. A price of zero SHALL be accepted.

#### Scenario: Negative price

- **WHEN** a client adds a product with price -1
- **THEN** the response status is 422
- **AND** the cart is left unchanged

#### Scenario: Missing required field

- **WHEN** a client adds a product whose payload omits `name`
- **THEN** the response status is 422
- **AND** the cart is left unchanged

#### Scenario: Zero price is valid

- **WHEN** a client adds a product with price 0
- **THEN** the response status is 201
- **AND** the returned cart has a line for that product with subtotal 0

### Requirement: Domain errors map to HTTP status codes

The API SHALL translate domain-level failures into HTTP responses rather than surfacing them as unhandled server errors. A request naming a product absent from the cart SHALL yield 404. No documented client-facing failure SHALL produce a 500.

#### Scenario: Missing product does not produce a server error

- **WHEN** a client removes a product identifier absent from the cart
- **THEN** the response status is 404, not 500

#### Scenario: Error body is structured JSON

- **WHEN** the API returns a 404 for a missing product
- **THEN** the body is JSON containing a `detail` field with a human-readable message
