from dataclasses import dataclass

from tienda.domain.cart import Cart
from tienda.domain.catalog import ProductCatalog
from tienda.domain.exceptions import InsufficientStock, ProductNotFound


@dataclass
class ConfirmLine:
    product_id: str
    quantity: int


def confirm_lines(lines: list[ConfirmLine], cart: Cart, catalog: ProductCatalog) -> None:
    quantities: dict[str, int] = {}
    for line in lines:
        quantities[line.product_id] = quantities.get(line.product_id, 0) + line.quantity

    for product_id, quantity in quantities.items():
        product = catalog.get(product_id)
        if product is None:
            raise ProductNotFound(product_id)
        if quantity > product.stock:
            raise InsufficientStock(product_id)

    for product_id, quantity in quantities.items():
        catalog.commit(product_id, quantity)
        cart.add(catalog.get(product_id), quantity)
