
from tienda.domain.cart import Cart
from tienda.domain.product import Product

def test_new_cart_is_total_zero():
    cart = Cart()

    assert cart.total == 0


def test_add_new_product_should_reflex_on_total():
    cart = Cart()

    new_product = Product("product_id", "pair of jeans", 3000)

    cart.add(new_product)

    assert cart.total == 3000


def test_add_same_product_twice_should_increase_quantity():
    cart = Cart()
    new_product = Product("product_id", "pair of jeans", 3000)

    cart.add(new_product)
    cart.add(new_product)
    
    assert cart.total == 6000

def test_remove_a_product_from_cart():
    cart = Cart()
    new_product = Product("product_id", "pair of jeans", 3000)
    cart.add(new_product)
    cart.remove(new_product)
    
    assert cart.total == 0
    assert cart.lines == {}