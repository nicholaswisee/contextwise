import pytest
from httpx import ASGITransport, AsyncClient

from contextwise.api.main import create_app
from contextwise.config import Settings

pytestmark = pytest.mark.integration


@pytest.fixture
def app_with_db(monkeypatch, apply_migrations):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://contextwise:contextwise@localhost:5434/contextwise_test"
    )
    return create_app(Settings())


@pytest.mark.asyncio
async def test_generate_returns_fake_provider_result_and_invocation(app_with_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        response = await client.post("/v1/generations", json={"prompt": "hello"})

        assert response.status_code == 200
        body = response.json()
        assert body["provider"] == "fake"
        assert body["fallback_used"] is False

        invocation = await client.get(f"/v1/invocations/{body['invocation_id']}")

    assert invocation.status_code == 200
    assert invocation.json()["status"] == "completed"
    assert invocation.json()["provider"] == "fake"


@pytest.mark.asyncio
async def test_generate_returns_validated_registered_schema(app_with_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        response = await client.post(
            "/v1/generations", json={"prompt": "hello", "response_schema": "answer"}
        )

    assert response.status_code == 200
    assert response.json()["structured"] == {"answer": "Hello from fake provider."}


@pytest.mark.asyncio
async def test_generate_rejects_unknown_model(app_with_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        response = await client.post(
            "/v1/generations", json={"prompt": "hello", "model": "missing"}
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "unknown model: missing"
