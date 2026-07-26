from fastapi import FastAPI

from tienda.api.schemas import CartLineOut, CartOut, ProductIn
from tienda.domain.cart import Cart
from tienda.domain.product import Product


app = FastAPI(title="Shop with python and TDD")
cart = Cart()


# Endpoints
@app.get("/cart", status_code=200)
def get_cart() -> CartOut:
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
def get_items(product_in: ProductIn):
    product = Product(product_in.product_id, product_in.name, product_in.price)
    cart.add(product)