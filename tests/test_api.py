from fastapi.testclient import TestClient
import pytest
from tienda.api.main import app, get_cart_repository
from tienda.domain.product import Product
from tienda.infrastructure.in_memory_cart_repository import InMemoryCartRepository

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_cart():
    repo = InMemoryCartRepository()
    app.dependency_overrides[get_cart_repository] = lambda: repo
    yield
    app.dependency_overrides.clear

client = TestClient(app)

@pytest.fixture(autouse=True)
def fresh_repository():                                             
    repo = InMemoryCartRepository()
    app.dependency_overrides[get_cart_repository] = lambda: repo
    yield repo                                                     
    app.dependency_overrides.clear()  


def test_get_empty_cart():
    response = client.get("/cart")
    assert response.status_code == 200
    assert response.json() == {"lines": [], "total": 0}

def test_get_cart_with_a_product(fresh_repository):
    fresh_repository.get().add(Product("product_id", "pair of jeans", 3000))
    response = client.get("/cart")

    assert response.status_code == 200
    assert response.json() == {
        "lines": [
            {"product_id": "product_id", "name": "pair of jeans", "price": 3000, "quantity": 1, "subtotal": 3000}
        ],
        "total": 3000,
    }

def test_add_product_via_post():
    response = client.post(
         "/cart/items",
        json={"product_id": "product_id", "name": "pair of jeans", "price": 3000},
    )

    assert response.status_code == 201

    cart_response = client.get("/cart")
    assert cart_response.json()["total"] == 3000