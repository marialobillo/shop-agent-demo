from fastapi.testclient import TestClient
from tienda.api.main import app

client = TestClient(app)

def test_get_empty_cart():
    response = client.get("/cart")
    assert response.status_code == 200
    assert response.json() == {"lines": {}, "total": 0}