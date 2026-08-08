from dataclasses import dataclass

@dataclass
class Product:
    product_id: str
    name: str
    price: int
    stock: int = 0

    def __post_init__(self):
        if self.price < 0:
            raise ValueError(f"Product Price must be zero o higher, got {self.price}")

