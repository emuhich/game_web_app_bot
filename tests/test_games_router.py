import pytest
from fastapi.testclient import TestClient
from app.main import app
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

client = TestClient(app)


@pytest.fixture(autouse=True)
def init_fastapi_cache():
    FastAPICache.init(InMemoryBackend(), prefix="test")
    yield
    FastAPICache.reset()


def test_categories_endpoint(monkeypatch):
    # Smoke test endpoint returns 200 and JSON
    resp = client.get("/games/honesty/categories")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
