import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_categories_endpoint(monkeypatch):
    # Smoke test endpoint returns 200 and JSON
    resp = client.get("/games/honesty/categories")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

