from dataclasses import dataclass

from tienda.domain.product import Product


@dataclass
class CartLine:
    product: Product
    quantity: int
    
    @property
    def subtotal(self) -> int:
        return self.product.price * self.quantity