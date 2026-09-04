from collections.abc import AsyncIterator
from typing import Any

from litellm import acompletion

from contextwise.application.llm.contracts import LLMRequest, LLMResult, LLMStreamChunk, LLMUsage
from contextwise.application.llm.errors import (
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMTransientError,
)


class LiteLLMClient:
    def __init__(self, provider: str, timeout_seconds: float):
        self.provider = provider
        self.timeout_seconds = timeout_seconds

    async def generate(self, request: LLMRequest) -> LLMResult:
        try:
            response = await acompletion(
                model=request.model,
                messages=self._messages(request),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format=request.response_schema,
                timeout=self.timeout_seconds,
            )
        except Exception as error:
            raise self._translate_error(error) from error

        usage = self._usage(response.usage)
        choice = response.choices[0]
        return LLMResult(
            text=choice.message.content or "",
            provider=self.provider,
            model=response.model or request.model,
            usage=usage,
            finish_reason=choice.finish_reason,
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        try:
            response = await acompletion(
                model=request.model,
                messages=self._messages(request),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format=request.response_schema,
                timeout=self.timeout_seconds,
                stream=True,
            )
            async for chunk in response:
                choice = chunk.choices[0] if chunk.choices else None
                if choice is None:
                    continue
                yield LLMStreamChunk(
                    text=choice.delta.content or "",
                    finish_reason=choice.finish_reason,
                    usage=self._usage(chunk.usage) if getattr(chunk, "usage", None) else None,
                )
        except Exception as error:
            raise self._translate_error(error) from error

    @staticmethod
    def _messages(request: LLMRequest) -> list[dict[str, str]]:
        return [{"role": message.role, "content": message.content} for message in request.messages]

    @staticmethod
    def _usage(usage: Any) -> LLMUsage:
        input_tokens = usage.prompt_tokens or 0
        output_tokens = usage.completion_tokens or 0
        total_tokens = usage.total_tokens or input_tokens + output_tokens
        return LLMUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    @staticmethod
    def _translate_error(error: Exception) -> LLMError:
        name = type(error).__name__.lower()
        message = str(error)
        if isinstance(error, TimeoutError) or "timeout" in name:
            return LLMTimeoutError(message)
        if "ratelimit" in name or "rate_limit" in name:
            return LLMRateLimitError(message)
        if "serviceunavailable" in name or "apierror" in name:
            return LLMTransientError(message)
        return LLMProviderError(message)
