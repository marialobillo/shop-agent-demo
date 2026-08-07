from dataclasses import dataclass
from typing import Protocol

from tienda.domain.product import Product


@dataclass
class ExtractedLine:
    source_text: str
    quantity: int
    product_id: str | None


class OrderExtractor(Protocol):
    def extract(self, text: str, products: list[Product]) -> list[ExtractedLine]: ...
