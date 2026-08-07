from tienda.domain.extraction import ExtractedLine, OrderExtractor
from tienda.domain.product import Product


class FakeOrderExtractor(OrderExtractor):
    def __init__(self, responses: dict[str, list[ExtractedLine]] | None = None):
        self._responses = responses or {}

    def extract(self, text: str, products: list[Product]) -> list[ExtractedLine]:
        return self._responses.get(text, [])
