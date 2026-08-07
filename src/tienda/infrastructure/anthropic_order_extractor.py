from anthropic import Anthropic

from tienda.domain.protocols.extraction import ExtractedLine
from tienda.domain.entities.product import Product

_TOOL_NAME = "extract_order_lines"


class AnthropicOrderExtractor:
    def __init__(self, client: Anthropic | None = None, model: str = "claude-sonnet-5"):
        self._client = client or Anthropic()
        self._model = model

    def extract(self, text: str, products: list[Product]) -> list[ExtractedLine]:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            tools=[self._build_tool(products)],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Store catalog:\n"
                        f"{self._render_catalog(products)}\n\n"
                        "Customer order request:\n"
                        f"{text}"
                    ),
                }
            ],
        )
        return self._parse_response(response)

    def _build_tool(self, products: list[Product]) -> dict:
        catalog_ids = [product.product_id for product in products]
        product_id_schema = {
            "type": ["string", "null"],
            "description": (
                "The matched catalog product id, or null if no single catalog "
                "product confidently matches this line."
            ),
        }
        if catalog_ids:
            product_id_schema["enum"] = [*catalog_ids, None]

        return {
            "name": _TOOL_NAME,
            "description": "Extract requested order lines from free text, matched against the given catalog.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "lines": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source_text": {
                                    "type": "string",
                                    "description": "The fragment of the input text this line was extracted from.",
                                },
                                "quantity": {"type": "integer", "minimum": 1},
                                "product_id": product_id_schema,
                            },
                            "required": ["source_text", "quantity", "product_id"],
                        },
                    }
                },
                "required": ["lines"],
            },
        }

    @staticmethod
    def _render_catalog(products: list[Product]) -> str:
        return "\n".join(
            f"- id={product.product_id} name={product.name!r} price={product.price}"
            for product in products
        )

    @staticmethod
    def _parse_response(response) -> list[ExtractedLine]:
        for block in response.content:
            if getattr(block, "type", None) == "tool_use" and block.name == _TOOL_NAME:
                return [
                    ExtractedLine(
                        source_text=line["source_text"],
                        quantity=line["quantity"],
                        product_id=line.get("product_id"),
                    )
                    for line in block.input.get("lines", [])
                ]
        return []
