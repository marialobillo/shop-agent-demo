from tienda.domain.entities.cart import Cart
from tienda.domain.protocols.repository import CartRepository


class InMemoryCartRepository(CartRepository):
    def __init__(self):
        self._cart = Cart()

    def get(self) -> Cart:
        return self._cart

    def save(self, cart: Cart) -> None:
        self._cart = cart