from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
import os

from tienda.infrastructure.order_extractors.anthropic_order_extractor import AnthropicOrderExtractor
from tienda.infrastructure.order_extractors.openrouter_order_extractor import OpenRouterOrderExtractor
from tienda.infrastructure.order_extractors.fake_order_extractor import FakeOrderExtractor
from tienda.api.mappers import cart_line_out, cart_to_out, suggested_order_to_out
from tienda.api.schemas import CartOut, ConfirmOrderIn, ErrorOut, ProductIn, SuggestedOrderOut, TextOrderIn
from tienda.domain.protocols.catalog import ProductCatalog
from tienda.domain.services.confirmation import ConfirmLine, confirm_lines
from tienda.domain.exceptions import InsufficientStock, ProductNotFound
from tienda.domain.protocols.extraction import OrderExtractor
from tienda.domain.entities.product import Product
from tienda.domain.protocols.repository import CartRepository
from tienda.domain.services.suggestion import suggest_lines
from tienda.infrastructure.order_extractors.anthropic_order_extractor import AnthropicOrderExtractor
from tienda.infrastructure.in_memory_cart_repository import InMemoryCartRepository
from tienda.infrastructure.in_memory_product_catalog import InMemoryProductCatalog

# Fixed seed catalog for this change; a real product-admin capability is out of scope.
_SEED_PRODUCTS = [
    Product("shirt-blue-m", "Blue Shirt - M", 1500, stock=20),
    Product("shirt-blue-l", "Blue Shirt - L", 1500, stock=15),
    Product("shirt-red-m", "Red Shirt - M", 1500, stock=10),
    Product("jeans-32", "Pair of Jeans - 32", 3000, stock=12),
    Product("jeans-34", "Pair of Jeans - 34", 3000, stock=8),
    Product("sneakers-42", "Sneakers - 42", 4500, stock=6),
]


def _build_order_extractor() -> OrderExtractor:
    provider = os.environ.get("ORDER_EXTRACTOR_PROVIDER", "fake")
    if provider == "anthropic":
        return AnthropicOrderExtractor()
    if provider == "openrouter":
        return OpenRouterOrderExtractor()
    if provider == "fake":
        return FakeOrderExtractor()
    raise ValueError(
        f"Unknown ORDER_EXTRACTOR_PROVIDER={provider!r}. "
        "Expected one of: anthropic, openrouter, fake."
    )

_repository = InMemoryCartRepository()
_catalog = InMemoryProductCatalog(_SEED_PRODUCTS)
_extractor = _build_order_extractor()

app = FastAPI(title="Shop with python and TDD")


# helpers
def get_cart_repository() -> CartRepository:
    return _repository

def get_product_catalog() -> ProductCatalog:
    return _catalog

def get_order_extractor() -> OrderExtractor:
    return _extractor


# Domain errors -> HTTP. Registered once so every route inherits the mapping,
# which is why the handlers below stay thin: call the domain, save, map.
@app.exception_handler(ProductNotFound)
def handle_product_not_found(request: Request, exc: ProductNotFound) -> JSONResponse:
    product_id = exc.args[0] if exc.args else "unknown"
    return JSONResponse(
        status_code=404,
        content={"detail": f"Product {product_id} not found"},
    )


@app.exception_handler(InsufficientStock)
def handle_insufficient_stock(request: Request, exc: InsufficientStock) -> JSONResponse:
    product_id = exc.args[0] if exc.args else "unknown"
    return JSONResponse(
        status_code=409,
        content={"detail": f"Insufficient stock for product {product_id}"},
    )


# Product enforces "price >= 0" itself and raises ValueError; the API only
# translates it. Product(...) is the sole ValueError-raising call in a route.
@app.exception_handler(ValueError)
def handle_invalid_value(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


# Endpoints
@app.get("/cart", status_code=200)
def get_cart(repo: CartRepository = Depends(get_cart_repository)) -> CartOut:
    return cart_to_out(repo.get())

@app.post("/cart/items", status_code=201)
def add_item(product_in: ProductIn, repo: CartRepository = Depends(get_cart_repository)) -> CartOut:
    cart = repo.get()
    cart.add(Product(product_in.product_id, product_in.name, product_in.price))
    repo.save(cart)
    return cart_to_out(cart)

@app.delete("/cart", status_code=200)
def clear_cart(repo: CartRepository = Depends(get_cart_repository)) -> CartOut:
    cart = repo.get()
    cart.clear()
    repo.save(cart)
    return cart_to_out(cart)

@app.delete("/cart/items/{product_id}", status_code=200, responses={404: {"model": ErrorOut}})
def remove_item(product_id: str, repo: CartRepository = Depends(get_cart_repository)) -> CartOut:
    cart = repo.get()
    line = cart.lines.get(product_id)
    if line is None:
        raise ProductNotFound(product_id)
    cart.remove(line.product)
    repo.save(cart)
    return cart_to_out(cart)

@app.post("/cart/from-text", status_code=200)
def suggest_from_text(
    order_in: TextOrderIn,
    catalog: ProductCatalog = Depends(get_product_catalog),
    extractor: OrderExtractor = Depends(get_order_extractor),
) -> SuggestedOrderOut:
    suggestions = suggest_lines(order_in.text, extractor, catalog)
    return suggested_order_to_out(suggestions)

@app.post("/cart/confirm", status_code=200, responses={404: {"model": ErrorOut}, 409: {"model": ErrorOut}})
def confirm_order(
    order_in: ConfirmOrderIn,
    repo: CartRepository = Depends(get_cart_repository),
    catalog: ProductCatalog = Depends(get_product_catalog),
) -> CartOut:
    cart = repo.get()
    lines = [ConfirmLine(line.product_id, line.quantity) for line in order_in.lines]
    confirm_lines(lines, cart, catalog)
    repo.save(cart)
    return cart_to_out(cart)


@app.get("/cart/items/{product_id}", status_code=200)
def get_cartline(product_id: str, repo: CartRepository = Depends(get_cart_repository)):
    cart = repo.get()
    cartline = cart.lines.get(product_id)
    if cartline:
        return cart_line_out(cartline)
    raise ProductNotFound(product_id)