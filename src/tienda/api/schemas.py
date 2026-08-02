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
    # price stays a plain int on purpose: the "price >= 0" rule belongs to
    # Product, and the API translates its ValueError instead of restating it.
    product_id: str
    name: str
    price: int

class ErrorOut(BaseModel):
    detail: str
