import pytest

from tienda.domain.entities.product import Product



def test_product_price_should_be_positive_or_zero():
    with pytest.raises(ValueError):
        Product("product_id", "pair of jeans", -3000)

def test_product_price_can_be_zero():
    new_product = Product("product_id", "pair of jeans", 0)

    assert new_product.price == 0

def test_product_stock_defaults_to_zero():
    new_product = Product("product_id", "pair of jeans", 3000)

    assert new_product.stock == 0

def test_product_stock_can_be_set():
    new_product = Product("product_id", "pair of jeans", 3000, stock=5)

    assert new_product.stock == 5