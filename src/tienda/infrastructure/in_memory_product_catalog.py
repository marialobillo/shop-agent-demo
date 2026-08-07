from tienda.domain.protocols.catalog import ProductCatalog
from tienda.domain.exceptions import InsufficientStock, ProductNotFound
from tienda.domain.entities.product import Product


class InMemoryProductCatalog(ProductCatalog):
    def __init__(self, products: list[Product]):
        self._products = {product.product_id: product for product in products}

    def list_products(self) -> list[Product]:
        return list(self._products.values())

    def get(self, product_id: str) -> Product | None:
        return self._products.get(product_id)

    def commit(self, product_id: str, quantity: int) -> None:
        product = self._products.get(product_id)
        if product is None:
            raise ProductNotFound(product_id)
        if quantity > product.stock:
            raise InsufficientStock(product_id)
        product.stock -= quantity
