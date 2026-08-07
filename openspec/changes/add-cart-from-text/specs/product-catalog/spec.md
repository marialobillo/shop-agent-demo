## Purpose

A queryable catalog of the store's products and their stock, used both as the context handed to the text-extraction LLM and as the authoritative source used to validate suggested cart lines and to decrement stock on confirm.

## ADDED Requirements

### Requirement: Catalog exposes available products
The catalog SHALL provide the full set of products currently offered by the store, including each product's id, name, price, and current stock quantity.

#### Scenario: Listing products for extraction context
- **WHEN** the catalog is queried for its products
- **THEN** it returns every product with its id, name, price, and current stock

### Requirement: Catalog validates a product reference
The catalog SHALL be able to confirm whether a given product id refers to a real product and, if so, return its authoritative name, price, and current stock.

#### Scenario: Reference to an existing product
- **WHEN** the catalog is asked to validate a product id that exists
- **THEN** it returns that product's authoritative name, price, and current stock

#### Scenario: Reference to a non-existent product
- **WHEN** the catalog is asked to validate a product id that does not exist
- **THEN** it reports the product as not found

### Requirement: Stock is only decremented on confirm
The catalog SHALL only reduce a product's stock when a confirmed quantity is committed against it. Generating or listing suggestions SHALL NOT change stock.

#### Scenario: Confirming a quantity reduces stock
- **WHEN** a quantity of a product is committed against the catalog
- **THEN** that product's stock is reduced by that quantity

#### Scenario: Suggestions do not affect stock
- **WHEN** products are looked up or validated for suggestion purposes only
- **THEN** stock levels are unchanged

### Requirement: Catalog rejects commits that exceed available stock
The catalog SHALL refuse to commit a quantity against a product when that quantity exceeds the product's current stock, and SHALL leave stock unchanged when it refuses.

#### Scenario: Requested quantity exceeds stock
- **WHEN** a commit is attempted for a quantity greater than the product's current stock
- **THEN** the commit is rejected with an insufficient-stock error and stock is left unchanged
