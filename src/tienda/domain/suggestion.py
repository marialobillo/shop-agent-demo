from dataclasses import dataclass
from typing import Literal

from tienda.domain.catalog import ProductCatalog
from tienda.domain.extraction import OrderExtractor
from tienda.domain.product import Product


@dataclass
class SuggestedLine:
    status: Literal["pending", "unmatched"]
    source_text: str
    quantity: int
    product: Product | None


def suggest_lines(text: str, extractor: OrderExtractor, catalog: ProductCatalog) -> list[SuggestedLine]:
    products = catalog.list_products()
    extracted_lines = extractor.extract(text, products)

    suggestions = []
    for line in extracted_lines:
        product = catalog.get(line.product_id) if line.product_id is not None else None
        if product is None:
            suggestions.append(SuggestedLine("unmatched", line.source_text, line.quantity, None))
        else:
            suggestions.append(SuggestedLine("pending", line.source_text, line.quantity, product))
    return suggestions
