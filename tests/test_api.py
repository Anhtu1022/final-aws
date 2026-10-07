import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["docs_url"] == "/docs"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database_connected" in data


def test_create_and_get_item():
    payload = {
        "title": "AWS Cloud Assignment Demo",
        "description": "Verifying RDS PostgreSQL persistence"
    }
    create_resp = client.post("/items/", json=payload)
    assert create_resp.status_code == 201
    created_item = create_resp.json()
    assert created_item["title"] == payload["title"]
    assert "id" in created_item

    item_id = created_item["id"]
    get_resp = client.get(f"/items/{item_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == item_id


def test_list_items():
    response = client.get("/items/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_files():
    response = client.get("/files/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
