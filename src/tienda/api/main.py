from fastapi import FastAPI

from tienda.domain.cart import Cart

app = FastAPI(title="Shop with python and TDD")
cart = Cart()


# Endpoints
@app.get("/cart", status_code=200)
def get_cart():
    return {"lines": cart.lines, "total": cart.total}    
