from collections.abc import AsyncIterator

from contextwise.application.llm.contracts import LLMRequest, LLMResult, LLMStreamChunk, LLMUsage
from contextwise.application.llm.errors import LLMError


class FakeLLMClient:
    def __init__(
        self,
        provider: str = "fake",
        text: str = "Hello from fake provider.",
        stream_chunks: tuple[str, ...] | None = None,
        failures: tuple[LLMError, ...] = (),
    ):
        self.provider = provider
        self.text = text
        self.stream_chunks = stream_chunks or (text,)
        self.failures = list(failures)
        self.calls: list[LLMRequest] = []

    async def generate(self, request: LLMRequest) -> LLMResult:
        self.calls.append(request)
        self._raise_next_failure()
        return LLMResult(
            text=self.text,
            provider=self.provider,
            model=request.model,
            usage=self._usage(request, self.text),
            finish_reason="stop",
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        self.calls.append(request)
        self._raise_next_failure()
        for text in self.stream_chunks:
            yield LLMStreamChunk(text=text)
        yield LLMStreamChunk(
            finish_reason="stop",
            usage=self._usage(request, "".join(self.stream_chunks)),
        )

    def _raise_next_failure(self) -> None:
        if self.failures:
            raise self.failures.pop(0)

    @staticmethod
    def _usage(request: LLMRequest, output: str) -> LLMUsage:
        input_tokens = sum(len(message.content.split()) for message in request.messages)
        output_tokens = len(output.split())
        return LLMUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
