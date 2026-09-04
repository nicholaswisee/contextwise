import asyncio

import pytest

from contextwise.application.llm.errors import LLMStructuredOutputError, LLMTimeoutError
from contextwise.application.llm.fake_client import FakeLLMClient
from contextwise.application.llm.generation_service import GenerationInput, GenerationService
from contextwise.application.llm.model_registry import ModelRegistry
from contextwise.application.llm.prompt_registry import PromptRegistry
from contextwise.application.llm.schema_registry import SchemaRegistry
from contextwise.config import Settings


class FakeInvocationRepository:
    def __init__(self):
        self.started = []
        self.completed = []
        self.failed = []
        self.cancelled = []

    async def create_started(self, **kwargs):
        self.started.append(kwargs)
        return "invocation-1"

    async def complete(self, invocation_id, result, latency_ms, retry_count, fallback_used):
        self.completed.append((invocation_id, result, retry_count, fallback_used))

    async def fail(self, invocation_id, error, latency_ms, retry_count, fallback_used):
        self.failed.append((invocation_id, error, retry_count, fallback_used))

    async def cancel(self, invocation_id, latency_ms):
        self.cancelled.append((invocation_id, latency_ms))


def settings(**values):
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost/contextwise",
        **values,
    )


def service(primary, fallback=None, **setting_values):
    configured_settings = settings(**setting_values)
    return GenerationService(
        model_registry=ModelRegistry.from_settings(configured_settings),
        prompt_registry=PromptRegistry(),
        schema_registry=SchemaRegistry(),
        clients={"fake-default": primary, **({"fake-fallback": fallback} if fallback else {})},
        repository=FakeInvocationRepository(),
        max_retries=configured_settings.llm_max_retries,
        structured_repair_attempts=configured_settings.llm_structured_repair_attempts,
        fallback_model=configured_settings.llm_fallback_model,
    )


@pytest.mark.asyncio
async def test_generate_returns_fake_result_and_persists_completion():
    gateway = service(FakeLLMClient(text="generated"))

    result = await gateway.generate(GenerationInput(prompt="hello"), request_id="request-1")

    assert result.text == "generated"
    assert result.provider == "fake"
    assert result.invocation_id == "invocation-1"
    assert result.retry_count == 0
    assert result.fallback_used is False
    assert gateway.repository.completed[0][0] == "invocation-1"


@pytest.mark.asyncio
async def test_generate_retries_timeout_before_succeeding():
    client = FakeLLMClient(failures=(LLMTimeoutError("timeout"),), text="after retry")
    gateway = service(client, llm_max_retries=1)

    result = await gateway.generate(GenerationInput(prompt="hello"), request_id="request-1")

    assert result.text == "after retry"
    assert result.retry_count == 1
    assert len(client.calls) == 2


@pytest.mark.asyncio
async def test_generate_discloses_fallback_after_retryable_primary_failure():
    primary = FakeLLMClient(failures=(LLMTimeoutError("timeout"),))
    fallback = FakeLLMClient(text="fallback answer")
    gateway = service(
        primary,
        fallback,
        llm_max_retries=0,
        llm_fallback_model="fake-fallback",
        llm_models_json=(
            '[{"name":"fake-fallback","provider":"fake","model":"fake-fallback",'
            '"capabilities":["text","structured","stream"]}]'
        ),
    )

    result = await gateway.generate(GenerationInput(prompt="hello"), request_id="request-1")

    assert result.text == "fallback answer"
    assert result.fallback_used is True
    assert result.model == "fake-fallback"


@pytest.mark.asyncio
async def test_generate_rejects_invalid_structured_output_and_persists_failure():
    gateway = service(
        FakeLLMClient(structured_json="not json"), llm_structured_repair_attempts=0
    )

    with pytest.raises(LLMStructuredOutputError, match="structured_output_invalid"):
        await gateway.generate(
            GenerationInput(prompt="hello", response_schema="answer"), request_id="request-1"
        )

    assert gateway.repository.failed[0][1].code == "structured_output_invalid"


@pytest.mark.asyncio
async def test_stream_forwards_chunks_and_persists_completion():
    gateway = service(FakeLLMClient(stream_chunks=("one ", "two")))

    chunks = [
        chunk
        async for chunk in gateway.stream(GenerationInput(prompt="hello"), request_id="request-1")
    ]

    assert [chunk.text for chunk in chunks] == ["one ", "two", ""]
    assert chunks[-1].invocation_id == "invocation-1"
    assert gateway.repository.completed[0][0] == "invocation-1"


@pytest.mark.asyncio
async def test_stream_persists_partial_upstream_failure():
    gateway = service(
        FakeLLMClient(
            stream_chunks=("partial",), stream_failure=LLMTimeoutError("stream timed out")
        )
    )

    stream = gateway.stream(GenerationInput(prompt="hello"), request_id="request-1")

    assert (await anext(stream)).text == "partial"
    with pytest.raises(LLMTimeoutError, match="stream timed out"):
        await anext(stream)

    assert gateway.repository.failed[0][1].code == "timeout"


@pytest.mark.asyncio
async def test_stream_marks_invocation_cancelled_when_consumer_is_cancelled():
    started = asyncio.Event()
    release = asyncio.Event()

    class BlockingClient:
        async def generate(self, request):
            raise AssertionError("generate is not used for streaming")

        async def stream(self, request):
            started.set()
            await release.wait()
            yield None

    gateway = service(BlockingClient())
    stream = gateway.stream(GenerationInput(prompt="hello"), request_id="request-1")
    next_chunk = asyncio.create_task(anext(stream))

    await started.wait()
    next_chunk.cancel()
    with pytest.raises(asyncio.CancelledError):
        await next_chunk

    assert gateway.repository.cancelled[0][0] == "invocation-1"
