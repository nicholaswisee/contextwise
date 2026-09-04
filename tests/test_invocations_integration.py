from datetime import datetime

import pytest

from contextwise.application.llm.contracts import LLMResult, LLMUsage
from contextwise.application.llm.errors import LLMProviderError
from contextwise.config import Settings
from contextwise.infrastructure.database import Database
from contextwise.infrastructure.invocations import InvocationRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repository(monkeypatch, apply_migrations):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://contextwise:contextwise@localhost:5434/contextwise_test",
    )
    database = Database(Settings())
    return InvocationRepository(database.session_factory)


@pytest.mark.asyncio
async def test_repository_persists_completed_invocation(repository):
    invocation_id = await repository.create_started(
        request_id="request-1",
        provider="fake",
        model="fake-default",
        prompt_name="direct",
        prompt_version=1,
    )

    await repository.complete(
        invocation_id,
        LLMResult(
            text="response",
            provider="fake",
            model="fake-default",
            usage=LLMUsage(input_tokens=1, output_tokens=2, total_tokens=3),
            finish_reason="stop",
        ),
        latency_ms=12,
        retry_count=1,
        fallback_used=False,
    )

    invocation = await repository.get(invocation_id)

    assert invocation is not None
    assert invocation.status == "completed"
    assert invocation.total_tokens == 3
    assert invocation.latency_ms == 12
    assert invocation.completed_at is not None


@pytest.mark.asyncio
async def test_repository_redacts_provider_error_message(repository):
    invocation_id = await repository.create_started(
        request_id="request-2",
        provider="fake",
        model="fake-default",
        prompt_name=None,
        prompt_version=None,
    )

    await repository.fail(
        invocation_id,
        LLMProviderError("api_key=super-secret"),
        latency_ms=3,
        retry_count=0,
        fallback_used=False,
    )

    invocation = await repository.get(invocation_id)

    assert invocation is not None
    assert invocation.status == "failed"
    assert invocation.error_code == "provider_error"
    assert invocation.error_message == "provider_error"
    assert "super-secret" not in invocation.error_message


@pytest.mark.asyncio
async def test_repository_marks_cancelled_invocation(repository):
    invocation_id = await repository.create_started(
        request_id="request-3",
        provider="fake",
        model="fake-default",
        prompt_name=None,
        prompt_version=None,
    )

    await repository.cancel(invocation_id, latency_ms=7)

    invocation = await repository.get(invocation_id)

    assert invocation is not None
    assert invocation.status == "cancelled"
    assert invocation.latency_ms == 7
    assert isinstance(invocation.completed_at, datetime)
