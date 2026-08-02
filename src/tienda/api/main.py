from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from tienda.api.mappers import cart_to_out
from tienda.api.schemas import CartOut, ErrorOut, ProductIn
from tienda.domain.exceptions import ProductNotFound
from tienda.domain.product import Product
from tienda.domain.repository import CartRepository
from tienda.infrastructure.in_memory_cart_repository import InMemoryCartRepository

_repository = InMemoryCartRepository()
app = FastAPI(title="Shop with python and TDD")


# helpers
def get_cart_repository() -> CartRepository:
    return _repository


# Domain errors -> HTTP. Registered once so every route inherits the mapping,
# which is why the handlers below stay thin: call the domain, save, map.
@app.exception_handler(ProductNotFound)
def handle_product_not_found(request: Request, exc: ProductNotFound) -> JSONResponse:
    product_id = exc.args[0] if exc.args else "unknown"
    return JSONResponse(
        status_code=404,
        content={"detail": f"Product {product_id} not found in cart"},
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
