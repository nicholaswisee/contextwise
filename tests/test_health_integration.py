import os
import subprocess

import pytest
from httpx import ASGITransport, AsyncClient

from contextwise.api.main import create_app
from contextwise.config import Settings


def get_test_database_url():
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://contextwise:contextwise@localhost:5434/contextwise_test",
    )


@pytest.fixture
async def app_with_db(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", get_test_database_url())
    settings = Settings()
    return create_app(settings)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ready_returns_ok_when_db_and_migrations_up(app_with_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_still_ok_when_db_up(app_with_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.integration
def test_migrations_are_idempotent():
    url = get_test_database_url()
    os.environ["DATABASE_URL"] = url
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], check=True)
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], check=True)
