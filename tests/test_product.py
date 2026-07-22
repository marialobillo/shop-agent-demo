import pytest

from tienda.domain.product import Product



def test_product_price_should_be_positive_or_zero():
    with pytest.raises(ValueError):
        Product("product_id", "pair of jeans", -3000)

def test_product_price_can_be_zero():
    new_product = Product("product_id", "pair of jeans", 0)

    assert new_product.price == 0