from tienda.domain.protocols.extraction import ExtractedLine
from tienda.domain.entities.product import Product


class FakeOrderExtractor:
    """Deterministic extractor for tests and no-API-key demos.

    Matches products by simple case-insensitive substring match between
    the input text and each product's name. Not meant to handle real
    natural-language variation — that's what the real extractors are for.
    """

    def extract(self, text: str, products: list[Product]) -> list[ExtractedLine]:
        lowered_text =text.lower()
        lines: list[ExtractedLine] = []
        for product in products:
            if product.name.lower() in lowered_text:
                lines.append(
                    ExtractedLine(
                        source_text=product.name,
                        quantity=1,
                        product_id=product.product_id,
                    )
                )
        return lines
    