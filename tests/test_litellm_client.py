from types import SimpleNamespace

import pytest

from contextwise.application.llm.contracts import LLMMessage, LLMRequest
from contextwise.application.llm.errors import LLMRateLimitError, LLMTimeoutError
from contextwise.application.llm.schema_registry import Answer
from contextwise.infrastructure.llm.litellm_client import LiteLLMClient


def request(response_schema=None) -> LLMRequest:
    return LLMRequest(
        model="openai/gpt-test",
        messages=(LLMMessage(role="user", content="hello"),),
        response_schema=response_schema,
    )


@pytest.mark.asyncio
async def test_generate_translates_request_and_response(monkeypatch):
    captured = {}

    async def completion(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="hi"), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=2, completion_tokens=3, total_tokens=5),
            model="gpt-test",
        )

    monkeypatch.setattr("contextwise.infrastructure.llm.litellm_client.acompletion", completion)

    result = await LiteLLMClient(provider="openai", timeout_seconds=10).generate(request(Answer))

    assert captured["model"] == "openai/gpt-test"
    assert captured["messages"] == [{"role": "user", "content": "hello"}]
    assert captured["response_format"] is Answer
    assert result.text == "hi"
    assert result.usage.total_tokens == 5


@pytest.mark.asyncio
async def test_generate_maps_timeout_to_internal_error(monkeypatch):
    async def completion(**kwargs):
        raise TimeoutError("upstream timeout")

    monkeypatch.setattr("contextwise.infrastructure.llm.litellm_client.acompletion", completion)

    with pytest.raises(LLMTimeoutError, match="upstream timeout"):
        await LiteLLMClient(provider="openai", timeout_seconds=10).generate(request())


@pytest.mark.asyncio
async def test_generate_maps_rate_limit_to_internal_error(monkeypatch):
    class RateLimitError(Exception):
        pass

    async def completion(**kwargs):
        raise RateLimitError("slow down")

    monkeypatch.setattr("contextwise.infrastructure.llm.litellm_client.acompletion", completion)

    with pytest.raises(LLMRateLimitError, match="slow down"):
        await LiteLLMClient(provider="openai", timeout_seconds=10).generate(request())


@pytest.mark.asyncio
async def test_stream_translates_text_and_final_usage(monkeypatch):
    async def stream():
        yield SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content="hello "), finish_reason=None)]
        )
        yield SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content="world"), finish_reason="stop")],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=2, total_tokens=3),
        )

    async def completion(**kwargs):
        assert kwargs["stream"] is True
        return stream()

    monkeypatch.setattr("contextwise.infrastructure.llm.litellm_client.acompletion", completion)

    chunks = [
        chunk
        async for chunk in LiteLLMClient(provider="openai", timeout_seconds=10).stream(request())
    ]

    assert [chunk.text for chunk in chunks] == ["hello ", "world"]
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.total_tokens == 3
