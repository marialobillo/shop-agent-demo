from fastapi import FastAPI

from tienda.api.schemas import CartLineOut, CartOut
from tienda.domain.cart import Cart


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
