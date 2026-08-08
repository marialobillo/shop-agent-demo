from typing import Literal

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

class TextOrderIn(BaseModel):
    text: str

class SuggestedLineOut(BaseModel):
    status: Literal["pending", "unmatched"]
    source_text: str
    quantity: int
    product_id: str | None = None
    name: str | None = None
    price: int | None = None
    subtotal: int | None = None

class SuggestedOrderOut(BaseModel):
    lines: list[SuggestedLineOut]

class ConfirmLineIn(BaseModel):
    product_id: str
    quantity: int

class ConfirmOrderIn(BaseModel):
    lines: list[ConfirmLineIn]
