import json
from collections.abc import AsyncIterator

from contextwise.application.llm.contracts import LLMRequest, LLMResult, LLMStreamChunk, LLMUsage
from contextwise.application.llm.errors import LLMError


class FakeLLMClient:
    def __init__(
        self,
        provider: str = "fake",
        text: str = "Hello from fake provider.",
        structured_json: str | None = None,
        stream_chunks: tuple[str, ...] | None = None,
        stream_failure: LLMError | None = None,
        failures: tuple[LLMError, ...] = (),
    ):
        self.provider = provider
        self.text = text
        self.structured_json = structured_json
        self.stream_chunks = stream_chunks or (text,)
        self.stream_failure = stream_failure
        self.failures = list(failures)
        self.calls: list[LLMRequest] = []

    async def generate(self, request: LLMRequest) -> LLMResult:
        self.calls.append(request)
        self._raise_next_failure()
        text = self._structured_text(request)
        return LLMResult(
            text=text,
            provider=self.provider,
            model=request.model,
            usage=self._usage(request, text),
            finish_reason="stop",
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        self.calls.append(request)
        self._raise_next_failure()
        for index, text in enumerate(self.stream_chunks, start=1):
            yield LLMStreamChunk(text=text)
            if self.stream_failure and index == 1:
                raise self.stream_failure
        yield LLMStreamChunk(
            finish_reason="stop",
            usage=self._usage(request, "".join(self.stream_chunks)),
        )

    def _raise_next_failure(self) -> None:
        if self.failures:
            raise self.failures.pop(0)

    def _structured_text(self, request: LLMRequest) -> str:
        if request.response_schema is None:
            return self.text
        if self.structured_json is not None:
            return self.structured_json
        field_name = next(iter(request.response_schema.model_fields))
        return json.dumps({field_name: self.text})

    @staticmethod
    def _usage(request: LLMRequest, output: str) -> LLMUsage:
        input_tokens = sum(len(message.content.split()) for message in request.messages)
        output_tokens = len(output.split())
        return LLMUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
