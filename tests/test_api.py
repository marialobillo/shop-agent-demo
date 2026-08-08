from fastapi.testclient import TestClient
import pytest
from tienda.api.main import app, get_cart_repository, get_order_extractor, get_product_catalog
from tienda.domain.protocols.extraction import ExtractedLine
from tienda.domain.entities.product import Product
from tienda.infrastructure.fake_order_extractor import FakeOrderExtractor
from tienda.infrastructure.in_memory_cart_repository import InMemoryCartRepository
from tienda.infrastructure.in_memory_product_catalog import InMemoryProductCatalog

client = TestClient(app)

@pytest.fixture(autouse=True)
def fresh_repository():
    repo = InMemoryCartRepository()
    app.dependency_overrides[get_cart_repository] = lambda: repo
    yield repo
    app.dependency_overrides.clear()

def test_get_cart_line_by_productId(fresh_repository):
    client.post("/cart/items", json={"product_id": "product_id", "name": "pair of jeans", "price": 3000})
    response = client.get("/cart/items/product_id")

    assert response.status_code == 200
    assert response.json() == {
        "product_id": "product_id",
        "name": "pair of jeans",
        "price": 3000,
        "quantity": 1,
        "subtotal": 3000,
    }

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


def test_remove_absent_product_returns_404_not_500():
    response = client.delete("/cart/items/absent_id")

    assert response.status_code == 404
    # An unmatched route would also answer 404, so pin the message: it must be
    # the domain error naming the product, not Starlette's default "Not Found".
    assert "absent_id" in response.json()["detail"]


def test_remove_one_unit_of_a_product_held_twice(fresh_repository):
    cart = fresh_repository.get()
    cart.add(Product("product_id", "pair of jeans", 3000))
    cart.add(Product("product_id", "pair of jeans", 3000))

    response = client.delete("/cart/items/product_id")

    assert response.status_code == 200
    assert response.json() == {
        "lines": [
            {"product_id": "product_id", "name": "pair of jeans", "price": 3000, "quantity": 1, "subtotal": 3000}
        ],
        "total": 3000,
    }


def test_remove_last_unit_drops_the_line(fresh_repository):
    fresh_repository.get().add(Product("product_id", "pair of jeans", 3000))

    response = client.delete("/cart/items/product_id")

    assert response.status_code == 200
    assert response.json() == {"lines": [], "total": 0}


def test_remove_absent_product_leaves_the_cart_unchanged(fresh_repository):
    fresh_repository.get().add(Product("product_id", "pair of jeans", 3000))

    response = client.delete("/cart/items/other_id")

    assert response.status_code == 404
    assert client.get("/cart").json()["total"] == 3000


def test_clear_cart_holding_products(fresh_repository):
    cart = fresh_repository.get()
    cart.add(Product("product_id", "pair of jeans", 3000))
    cart.add(Product("product_2id", "red t-shirt", 2000))

    response = client.delete("/cart")

    assert response.status_code == 200
    assert response.json() == {"lines": [], "total": 0}
    assert client.get("/cart").json() == {"lines": [], "total": 0}


def test_clear_an_already_empty_cart():
    response = client.delete("/cart")

    assert response.status_code == 200
    assert response.json() == {"lines": [], "total": 0}


# The two 422 paths differ in body shape on purpose: a negative price is
# refused by Product and carries a string detail, a missing field is refused
# by pydantic and carries a list. Only the status and the cart are asserted.
def test_negative_price_is_rejected_by_the_domain():
    response = client.post(
        "/cart/items",
        json={"product_id": "product_id", "name": "pair of jeans", "price": -1},
    )

    assert response.status_code == 422
    assert client.get("/cart").json() == {"lines": [], "total": 0}


def test_payload_missing_a_field_is_rejected():
    response = client.post(
        "/cart/items",
        json={"product_id": "product_id", "price": 3000},
    )

    assert response.status_code == 422
    assert client.get("/cart").json() == {"lines": [], "total": 0}


def test_zero_price_is_accepted():
    response = client.post(
        "/cart/items",
        json={"product_id": "freebie", "name": "sticker", "price": 0},
    )

    assert response.status_code == 201
    assert response.json() == {
        "lines": [
            {"product_id": "freebie", "name": "sticker", "price": 0, "quantity": 1, "subtotal": 0}
        ],
        "total": 0,
    }


def test_get_cart_with_two_distinct_products(fresh_repository):
    cart = fresh_repository.get()
    cart.add(Product("product_id", "pair of jeans", 3000))
    cart.add(Product("product_2id", "red t-shirt", 2000))

    body = client.get("/cart").json()

    assert len(body["lines"]) == 2
    assert body["total"] == sum(line["subtotal"] for line in body["lines"])
    assert body["total"] == 5000


def test_add_same_product_twice_keeps_one_line():
    payload = {"product_id": "product_id", "name": "pair of jeans", "price": 3000}
    client.post("/cart/items", json=payload)
    response = client.post("/cart/items", json=payload)

    assert response.status_code == 201
    assert response.json() == {
        "lines": [
            {"product_id": "product_id", "name": "pair of jeans", "price": 3000, "quantity": 2, "subtotal": 6000}
        ],
        "total": 6000,
    }


def test_from_text_returns_pending_line_for_a_known_product(fresh_repository):
    jeans = Product("jeans", "pair of jeans", 3000, stock=5)
    catalog = InMemoryProductCatalog([jeans])
    extractor = FakeOrderExtractor({"a pair of jeans": [ExtractedLine("a pair of jeans", 1, "jeans")]})
    app.dependency_overrides[get_product_catalog] = lambda: catalog
    app.dependency_overrides[get_order_extractor] = lambda: extractor

    response = client.post("/cart/from-text", json={"text": "a pair of jeans"})

    assert response.status_code == 200
    assert response.json() == {
        "lines": [
            {
                "status": "pending",
                "source_text": "a pair of jeans",
                "quantity": 1,
                "product_id": "jeans",
                "name": "pair of jeans",
                "price": 3000,
                "subtotal": 3000,
            }
        ]
    }


def test_from_text_returns_unmatched_line_for_unknown_text(fresh_repository):
    catalog = InMemoryProductCatalog([])
    extractor = FakeOrderExtractor({"a unicorn": [ExtractedLine("a unicorn", 1, None)]})
    app.dependency_overrides[get_product_catalog] = lambda: catalog
    app.dependency_overrides[get_order_extractor] = lambda: extractor

    response = client.post("/cart/from-text", json={"text": "a unicorn"})

    assert response.status_code == 200
    assert response.json() == {
        "lines": [
            {
                "status": "unmatched",
                "source_text": "a unicorn",
                "quantity": 1,
                "product_id": None,
                "name": None,
                "price": None,
                "subtotal": None,
            }
        ]
    }


def test_from_text_does_not_change_the_cart(fresh_repository):
    jeans = Product("jeans", "pair of jeans", 3000, stock=5)
    catalog = InMemoryProductCatalog([jeans])
    extractor = FakeOrderExtractor({"a pair of jeans": [ExtractedLine("a pair of jeans", 1, "jeans")]})
    app.dependency_overrides[get_product_catalog] = lambda: catalog
    app.dependency_overrides[get_order_extractor] = lambda: extractor

    client.post("/cart/from-text", json={"text": "a pair of jeans"})

    assert client.get("/cart").json() == {"lines": [], "total": 0}


def test_confirm_adds_lines_to_the_cart_and_reduces_stock(fresh_repository):
    jeans = Product("jeans", "pair of jeans", 3000, stock=5)
    catalog = InMemoryProductCatalog([jeans])
    app.dependency_overrides[get_product_catalog] = lambda: catalog

    response = client.post("/cart/confirm", json={"lines": [{"product_id": "jeans", "quantity": 2}]})

    assert response.status_code == 200
    assert response.json() == {
        "lines": [
            {"product_id": "jeans", "name": "pair of jeans", "price": 3000, "quantity": 2, "subtotal": 6000}
        ],
        "total": 6000,
    }
    assert catalog.get("jeans").stock == 3


def test_confirm_with_insufficient_stock_rejects_and_leaves_cart_unchanged(fresh_repository):
    jeans = Product("jeans", "pair of jeans", 3000, stock=1)
    catalog = InMemoryProductCatalog([jeans])
    app.dependency_overrides[get_product_catalog] = lambda: catalog

    response = client.post("/cart/confirm", json={"lines": [{"product_id": "jeans", "quantity": 2}]})

    assert response.status_code == 409
    assert "jeans" in response.json()["detail"]
    assert client.get("/cart").json() == {"lines": [], "total": 0}
    assert catalog.get("jeans").stock == 1


def test_confirm_with_unknown_product_returns_404_and_leaves_cart_unchanged(fresh_repository):
    catalog = InMemoryProductCatalog([])
    app.dependency_overrides[get_product_catalog] = lambda: catalog

    response = client.post("/cart/confirm", json={"lines": [{"product_id": "unknown", "quantity": 1}]})

    assert response.status_code == 404
    assert "unknown" in response.json()["detail"]
    assert client.get("/cart").json() == {"lines": [], "total": 0}