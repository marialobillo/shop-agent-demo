
from http.client import HTTPException

from tienda.domain.cartline import CartLine
from tienda.domain.exceptions import ProductNotFound
from tienda.domain.product import Product


class Cart:
    def __init__(self):
        self.lines = {}


    @property
    def total(self) -> int:
        return sum(line.subtotal for line in self.lines.values())

    def add(self, product: Product):
        if product.product_id in self.lines:
            self.lines[product.product_id].quantity += 1
        else:
            line = CartLine(product, 1)   
            self.lines[product.product_id] = line
        
    def remove(self,product: Product):
        if product.product_id in self.lines:
            if self.lines[product.product_id].quantity > 1:
                self.lines[product.product_id].quantity -= 1
            else:
                del self.lines[product.product_id]
        else:
            raise ProductNotFound(product.product_id)
        
    def clear(self):
        self.lines.clear()