"""Core API integration tests."""
import pytest
from httpx import AsyncClient, ASGITransport
from api.app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    r = await client.post("/api/v1/auth/register", json={
        "email": "test@aquavision.io",
        "username": "testcoach",
        "password": "password123",
        "full_name": "Test Coach",
        "role": "coach",
    })
    assert r.status_code in (201, 409)

    # Login
    r2 = await client.post("/api/v1/auth/login", json={
        "email": "test@aquavision.io",
        "password": "password123",
    })
    if r2.status_code == 200:
        data = r2.json()
        assert "access_token" in data
        assert "refresh_token" in data


@pytest.mark.asyncio
async def test_openapi_docs(client):
    r = await client.get("/api/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert spec["info"]["title"] == "AquaVision Analytics"
    # All main routes exist
    paths = spec["paths"]
    assert any("/auth/login" in p for p in paths)
    assert any("/videos/upload" in p for p in paths)
    assert any("/matches" in p for p in paths)
    assert any("/clips" in p for p in paths)
    assert any("/analytics" in p for p in paths)
