from fastapi import Depends, FastAPI

from tienda.api.schemas import CartLineOut, CartOut, ProductIn
from tienda.domain.cart import Cart
from tienda.domain.product import Product
from tienda.infrastructure.in_memory_cart_repository import InMemoryCartRepository

_repository = InMemoryCartRepository()
app = FastAPI(title="Shop with python and TDD")
# cart = Cart()

# helpers
def get_cart_repository() -> InMemoryCartRepository:
    return _repository


# Endpoints
@app.get("/cart", status_code=200)
def get_cart(repo: InMemoryCartRepository = Depends(get_cart_repository)) -> CartOut:
    cart = repo.get()
    lines = [
        CartLineOut(
            product_id=line.product.product_id,
            name=line.product.name,
            price=line.product.price,
            quantity=line.quantity,
            subtotal=line.subtotal,
        )
        for line in cart.lines.values()
    ]
    return CartOut(lines=lines, total=cart.total)    

@app.post("/cart/items", status_code=201)
def get_items(product_in: ProductIn, repo: InMemoryCartRepository = Depends(get_cart_repository)) -> CartOut:
    cart = repo.get()
    product = Product(product_in.product_id, product_in.name, product_in.price)
    cart.add(product)
    cart_out = get_cart(repo)
    return cart_out