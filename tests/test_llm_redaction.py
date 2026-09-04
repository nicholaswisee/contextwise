import pytest

from contextwise.api.dependencies import get_generation_service
from contextwise.api.main import create_app
from contextwise.application.llm.errors import LLMProviderError
from contextwise.application.llm.generation_service import GenerationInput
from contextwise.config import Settings


class FailingGenerationService:
    async def generate(self, input: GenerationInput, request_id: str):
        raise LLMProviderError("api_key=super-secret")


@pytest.mark.asyncio
async def test_generation_error_response_redacts_provider_secret(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/contextwise")
    app = create_app(Settings())
    app.dependency_overrides[get_generation_service] = lambda: FailingGenerationService()

    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/v1/generations", json={"prompt": "hello"})

    assert response.status_code == 502
    assert response.json() == {"detail": "provider_error"}
    assert "super-secret" not in response.text
