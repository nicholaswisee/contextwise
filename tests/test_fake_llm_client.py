import pytest

from contextwise.application.llm.contracts import LLMMessage, LLMRequest
from contextwise.application.llm.errors import LLMTimeoutError
from contextwise.application.llm.fake_client import FakeLLMClient


def request() -> LLMRequest:
    return LLMRequest(
        model="fake-default",
        messages=(LLMMessage(role="user", content="hello fake provider"),),
    )


@pytest.mark.asyncio
async def test_generate_returns_deterministic_result_and_records_request():
    client = FakeLLMClient(text="fixed response")

    result = await client.generate(request())

    assert result.text == "fixed response"
    assert result.provider == "fake"
    assert result.model == "fake-default"
    assert result.usage.total_tokens == result.usage.input_tokens + result.usage.output_tokens
    assert client.calls == [request()]


@pytest.mark.asyncio
async def test_stream_yields_configured_chunks_and_final_usage():
    client = FakeLLMClient(stream_chunks=("one ", "two"))

    chunks = [chunk async for chunk in client.stream(request())]

    assert [chunk.text for chunk in chunks] == ["one ", "two", ""]
    assert chunks[-1].finish_reason == "stop"
    assert chunks[-1].usage is not None


@pytest.mark.asyncio
async def test_generate_raises_configured_failure_before_returning_result():
    client = FakeLLMClient(failures=(LLMTimeoutError("provider timed out"),))

    with pytest.raises(LLMTimeoutError, match="provider timed out"):
        await client.generate(request())

    assert client.calls == [request()]
