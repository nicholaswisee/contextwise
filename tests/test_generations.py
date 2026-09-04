import pytest
from httpx import ASGITransport, AsyncClient

from contextwise.api.main import create_app
from contextwise.config import Settings

pytestmark = pytest.mark.integration


@pytest.fixture
def app_with_db(monkeypatch, apply_migrations):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://contextwise:contextwise@localhost:5434/contextwise_test",
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
    assert invocation.json()["estimated_cost_usd"] == 0


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


@pytest.mark.asyncio
async def test_stream_emits_chunks_and_completion_event(app_with_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        response = await client.post("/v1/generations/stream", json={"prompt": "hello"})

    assert response.status_code == 200
    assert 'data: {"type": "chunk", "text": "Hello from fake provider."}' in response.text
    assert 'data: {"type": "completed", "invocation_id":' in response.text


@pytest.mark.asyncio
async def test_stream_rejects_structured_output_until_stream_validation_exists(app_with_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        response = await client.post(
            "/v1/generations/stream", json={"prompt": "hello", "response_schema": "answer"}
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "structured streaming is not supported"


@pytest.mark.asyncio
async def test_llm_registries_expose_models_and_prompt_versions(app_with_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db), base_url="http://test"
    ) as client:
        models = await client.get("/v1/models")
        prompts = await client.get("/v1/prompts")

    assert models.status_code == 200
    assert models.json()[0]["name"] == "fake-default"
    assert prompts.status_code == 200
    assert prompts.json() == [{"name": "direct", "version": 1}]
