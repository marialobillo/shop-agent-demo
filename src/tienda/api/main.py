from fastapi import FastAPI

from tienda.domain.cart import Cart

app = FastAPI(title="Shop with python and TDD")



# Endpoints
@app.get("/cart", status_code=200)
def new_cart():
    cart = Cart()
    return {"lines": cart.lines, "total": cart.total}    
