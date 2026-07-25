from fastapi.testclient import TestClient
from tienda.api.main import app, cart
from tienda.domain.product import Product

client = TestClient(app)

def test_get_empty_cart():
    response = client.get("/cart")
    assert response.status_code == 200
    assert response.json() == {"lines": [], "total": 0}

def test_get_cart_with_a_product():
    cart.add(Product("product_id", "pair of jeans", 3000))
    response = client.get("/cart")

    assert response.status_code == 200
    assert response.json() == {
        "lines": [
            {"product_id": "product_id", "name": "pair of jeans", "price": 3000, "quantity": 1, "subtotal": 3000}
        ],
        "total": 3000,
    }