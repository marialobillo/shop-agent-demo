## Purpose

Lets a customer describe an order in free text (e.g. "2 blue shirts size M and a pair of jeans") and get back catalog-validated suggested cart lines to review and confirm, instead of adding items one at a time by product id.

## ADDED Requirements

### Requirement: Free text is extracted into candidate order lines
The system SHALL accept a free-text description of a desired order and use LLM-based extraction to produce candidate lines, each referencing a product and a quantity.

#### Scenario: Text describing known products
- **WHEN** a customer submits free text naming two distinct products the store carries, each with a quantity
- **THEN** the system extracts two candidate lines, each with the correct product reference and quantity

#### Scenario: Text with no recognizable products
- **WHEN** a customer submits free text that names nothing the store carries
- **THEN** the system returns an empty list of suggested lines rather than an error

### Requirement: Suggested lines are validated against the real catalog before being shown
Every line returned from text extraction SHALL be checked against the real product catalog before being shown to the customer. A candidate that does not resolve to exactly one real catalog product SHALL be returned as unmatched rather than as a pending line for a guessed or non-existent product.

#### Scenario: Candidate matches a real product
- **WHEN** an extracted candidate line resolves to exactly one product that exists in the catalog
- **THEN** the returned suggested line uses that product's authoritative id, name, and price, with status `pending`

#### Scenario: Candidate does not match any real product
- **WHEN** an extracted candidate line does not correspond to any product in the catalog
- **THEN** the response marks that line as unmatched instead of returning it as a `pending` line

#### Scenario: Candidate matches more than one real product
- **WHEN** an extracted candidate line is ambiguous and matches more than one catalog product
- **THEN** the response marks that line as unmatched rather than guessing a single product

### Requirement: Suggested lines do not affect the cart or stock
Returning suggested `pending` lines from free text SHALL NOT add anything to the customer's cart and SHALL NOT change product stock.

#### Scenario: Cart is unchanged after a from-text request
- **WHEN** a customer submits free text and receives suggested pending lines
- **THEN** the customer's cart contents and totals are unchanged until those lines are confirmed

### Requirement: Pending lines can be confirmed into the cart
The system SHALL provide a way to confirm a set of previously suggested pending lines, turning each into a confirmed `CartLine` in the customer's cart and decrementing catalog stock by the confirmed quantities.

#### Scenario: Confirming pending lines updates the cart
- **WHEN** a customer confirms one or more pending lines
- **THEN** each becomes a confirmed `CartLine` in the cart and the cart total reflects them

#### Scenario: Confirming pending lines decrements stock
- **WHEN** a customer confirms a pending line for a given product and quantity
- **THEN** that product's stock in the catalog is reduced by that quantity

### Requirement: Confirm re-validates against current stock
Because stock is not reserved while a line is pending, confirming a line SHALL re-check current catalog stock at confirm time and SHALL reject the confirmation if stock is no longer sufficient.

#### Scenario: Stock became insufficient after the suggestion was made
- **WHEN** a customer confirms a pending line whose quantity now exceeds the product's current stock
- **THEN** the confirmation is rejected with an insufficient-stock error and the cart is left unchanged for that line
