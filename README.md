# Tienda — Chat-to-Cart Demo

A shopping cart with a hexagonal/ports-and-adapters architecture, extended
with an LLM-powered "chat to cart" feature: describe what you want to buy
in plain language, and the system extracts structured order lines against
a product catalog using tool calling.

## What it does

1. **Clean layered architecture**: `domain/` has zero knowledge of
   FastAPI, databases, or LLMs. Business rules (cart logic, order
   confirmation, stock checks) are pure Python, fully unit-tested in
   isolation.
2. **Provider-agnostic LLM integration**: the order-extraction feature
   is defined as a `Protocol` (`OrderExtractor`) in the domain layer.
   Swapping the underlying model is a matter of adding one new file in
   `infrastructure/order_extractors/` — no changes anywhere else in the
   codebase.

## Architecture

'''
src/tienda/
domain/
entities/ # Product, Cart, CartLine — pure business objects
protocols/ # Interfaces: CartRepository, ProductCatalog, OrderExtractor
services/ # confirmation.py, suggestion.py — business logic, no I/O
infrastructure/
order_extractors/ # OrderExtractor implementations, one per LLM provider
in_memory_cart_repository.py
in_memory_product_catalog.py
api/
main.py # FastAPI routes — thin, delegates to domain
'''


## Trying it out — no API key required

By default the app runs with `FakeOrderExtractor`, a simple deterministic
matcher (no LLM call, no cost, no setup):

```bash
uv sync
uv run uvicorn tienda.api.main:app --reload
```

```bash
curl -X POST http://localhost:8000/cart/from-text \
  -H "Content-Type: application/json" \
  -d '{"text": "I want a blue shirt in size M"}'
```

## Trying it out — no API key required

By default the app runs with `FakeOrderExtractor`, a simple deterministic
matcher (no LLM call, no cost, no setup):

```bash
uv sync
uv run uvicorn tienda.api.main:app --reload
```

Extract order lines from plain text (matches by product name substring
with the fake extractor):

```bash
curl -X POST http://localhost:8000/cart/from-text \
  -H "Content-Type: application/json" \
  -d '{"text": "I want a blue shirt in size M and a pair of jeans size 32"}'
```

Confirm the suggested lines into the actual cart:

```bash
curl -X POST http://localhost:8000/cart/confirm \
  -H "Content-Type: application/json" \
  -d '{"lines": [{"product_id": "shirt-blue-m", "quantity": 1}]}'
```


## Using a real LLM provider

Set `ORDER_EXTRACTOR_PROVIDER` in your environment:

| Value | Requires | Notes |
|---|---|---|
| `fake` (default) | nothing | deterministic substring match, for demos/tests |
| `openrouter` | `OPENROUTER_API_KEY` | uses a free-tier model with tool calling |
| `anthropic` | `ANTHROPIC_API_KEY` | uses Claude, real tool calling |

```bash
export ORDER_EXTRACTOR_PROVIDER=openrouter
export OPENROUTER_API_KEY=your-key-here
uv run uvicorn tienda.api.main:app --reload
```

## Adding a new provider

Implement the `OrderExtractor` protocol
(`src/tienda/domain/protocols/extraction.py`) in a new file under
`src/tienda/infrastructure/order_extractors/`, then add one branch to
`_build_order_extractor()` in `api/main.py`. No other file needs to
change — that's the point of the protocol boundary.

## Running tests

```bash
uv run pytest
```

Tests never call a real LLM — `FakeOrderExtractor` (or a stub) is used
throughout, so the suite runs offline and free.

## Tech stack

FastAPI, Python 3.13, `uv`, pytest, TDD — built change-by-change with
[OpenSpec](openspec/), see `openspec/changes/` for design docs per feature.

