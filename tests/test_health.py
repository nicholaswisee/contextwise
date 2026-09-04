import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from contextwise.api.main import create_app, lifespan
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


@pytest.mark.asyncio
async def test_shutdown_waits_for_active_request(app):
    request_started = asyncio.Event()
    release_request = asyncio.Event()

    @app.get("/slow")
    async def slow_request():
        request_started.set()
        await release_request.wait()
        return {"status": "done"}

    app_lifespan = lifespan(app)
    await app_lifespan.__aenter__()
    client = _client(app)
    await client.__aenter__()
    request_task = asyncio.create_task(client.get("/slow"))
    shutdown_task = None

    try:
        await request_started.wait()
        shutdown_task = asyncio.create_task(app_lifespan.__aexit__(None, None, None))
        await asyncio.sleep(0)
        assert not shutdown_task.done()

        release_request.set()
        response = await request_task
        await shutdown_task

        assert response.status_code == 200
        assert response.json() == {"status": "done"}
    finally:
        release_request.set()
        if not request_task.done():
            await request_task
        if shutdown_task is not None and not shutdown_task.done():
            await shutdown_task
        await client.__aexit__(None, None, None)
