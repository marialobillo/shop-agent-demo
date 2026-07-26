from pydantic import BaseModel


class CartLineOut(BaseModel):
    product_id: str
    name: str
    price: int
    quantity: int
    subtotal: int

class CartOut(BaseModel):
    lines: list[CartLineOut]
    total: int

class ProductIn(BaseModel):
    product_id: str
    name: str
    price: int