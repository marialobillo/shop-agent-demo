from tienda.domain.cartline import CartLine
from tienda.domain.exceptions import ProductNotFound
from tienda.domain.entities.product import Product


class Cart:
    def __init__(self):
        self.lines = {}

    @property
    def total(self) -> int:
        return sum(line.subtotal for line in self.lines.values())

    def add(self, product: Product, quantity: int = 1):
        if product.product_id in self.lines:
            self.lines[product.product_id].quantity += quantity
        else:
            line = CartLine(product, quantity)
            self.lines[product.product_id] = line
        
    def remove(self,product: Product):
        if product.product_id not in self.lines:    
            raise ProductNotFound(product.product_id)
        line = self.lines[product.product_id]
        if line.quantity > 1:
            line.quantity -= 1
        else:
            del self.lines[product.product_id]
        
    def clear(self):
        self.lines.clear()