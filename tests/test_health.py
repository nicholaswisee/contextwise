import pytest
from httpx import ASGITransport, AsyncClient

from contextwise.api.main import create_app
from contextwise.config import Settings


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    settings = Settings()
    return create_app(settings)


def _client(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_live_returns_ok(app):
    async with _client(app) as client:
        response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.asyncio
async def test_live_does_not_depend_on_database(app):
    # Even with a bogus database URL, liveness should succeed
    async with _client(app) as client:
        response = await client.get("/health/live")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ready_with_bad_database_returns_service_unavailable(app):
    async with _client(app) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_request_id_header_returned(app):
    async with _client(app) as client:
        response = await client.get("/health/live")
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"]
