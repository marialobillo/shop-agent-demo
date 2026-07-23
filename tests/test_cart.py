
from fastapi.testclient import TestClient
import pytest

from tienda.domain.cart import Cart
from tienda.domain.exceptions import ProductNotFound
from tienda.domain.product import Product
from tienda.api.main import app, cart

client = TestClient(app)

def test_new_cart_is_total_zero():
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

def test_remove_a_product_from_cart_that_not_exist():
    cart = Cart()
    new_product = Product("product_id", "pair of jeans", 3000)
    second_product = Product("product_2id", "red t-shirt", 2000)

    cart.add(new_product)
    
    with pytest.raises(ProductNotFound):
        cart.remove(second_product)

def test_remove_from_quantity_two_to_one():
    cart = Cart()
    new_product = Product("product_id", "pair of jeans", 3000)

    cart.add(new_product)
    cart.add(new_product)
    cart.remove(new_product)

    assert cart.total == 3000
    assert cart.lines["product_id"].quantity == 1

def test_remove_all_items_from_cart():
    cart = Cart()
    new_product = Product("product_id", "pair of jeans", 3000)
    second_product = Product("product_2id", "red t-shirt", 2000)

    cart.add(new_product)
    cart.add(second_product)
    cart.clear()

    assert cart.total == 0
    assert cart.lines == {}

def test_add_two_diff_products():
    cart = Cart()
    product_a = Product("product_id", "pair of jeans", 3000)
    product_b = Product("product_2id", "red t-shirt", 2000)

    cart.add(product_a)
    cart.add(product_b)

    assert cart.total == 5000
    assert len(cart.lines) == 2