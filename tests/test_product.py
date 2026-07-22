import pytest

from tienda.domain.product import Product



def test_product_price_should_be_positive_or_zero():
    with pytest.raises(ValueError):
        Product("product_id", "pair of jeans", -3000)