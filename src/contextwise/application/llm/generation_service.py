import asyncio
from collections.abc import AsyncIterator
from time import perf_counter
from typing import Protocol

from pydantic import BaseModel, TypeAdapter

from contextwise.application.llm.contracts import (
    LLMClient,
    LLMMessage,
    LLMRequest,
    LLMResult,
    LLMStreamChunk,
    LLMUsage,
)
from contextwise.application.llm.errors import LLMError, LLMStructuredOutputError
from contextwise.application.llm.model_registry import ModelRegistry
from contextwise.application.llm.prompt_registry import PromptRegistry
from contextwise.application.llm.schema_registry import SchemaRegistry


class InvocationStore(Protocol):
    async def create_started(
        self,
        request_id: str,
        provider: str,
        model: str,
        prompt_name: str | None,
        prompt_version: int | None,
    ) -> str: ...

    async def complete(
        self,
        invocation_id: str,
        result: LLMResult,
        latency_ms: int,
        retry_count: int,
        fallback_used: bool,
    ) -> None: ...

    async def fail(
        self,
        invocation_id: str,
        error: LLMError,
        latency_ms: int,
        retry_count: int,
        fallback_used: bool,
    ) -> None: ...

    async def cancel(self, invocation_id: str, latency_ms: int) -> None: ...


class GenerationInput(BaseModel):
    prompt: str
    model: str | None = None
    prompt_name: str | None = None
    prompt_version: int | None = None
    response_schema: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class GenerationOutput(BaseModel):
    invocation_id: str
    text: str
    structured: dict[str, object] | None
    provider: str
    model: str
    prompt_name: str | None
    prompt_version: int | None
    usage: LLMUsage
    latency_ms: int
    retry_count: int
    fallback_used: bool
    finish_reason: str | None


class GenerationService:
    def __init__(
        self,
        model_registry: ModelRegistry,
        prompt_registry: PromptRegistry,
        schema_registry: SchemaRegistry,
        clients: dict[str, LLMClient],
        repository: InvocationStore,
        max_retries: int,
        structured_repair_attempts: int,
        fallback_model: str | None,
    ):
        self.model_registry = model_registry
        self.prompt_registry = prompt_registry
        self.schema_registry = schema_registry
        self.clients = clients
        self.repository = repository
        self.max_retries = max_retries
        self.structured_repair_attempts = structured_repair_attempts
        self.fallback_model = fallback_model

    async def generate(self, input: GenerationInput, request_id: str) -> GenerationOutput:
        model_name = input.model or "fake-default"
        model = self.model_registry.get(model_name)
        prompt_name = input.prompt_name or "direct"
        prompt, prompt_version = self.prompt_registry.render(
            prompt_name, input.prompt_version, input.prompt
        )
        schema = self.schema_registry.get(input.response_schema) if input.response_schema else None
        request = LLMRequest(
            model=model.model,
            messages=(LLMMessage(role="user", content=prompt),),
            temperature=input.temperature,
            max_tokens=input.max_tokens,
            response_schema=schema,
        )
        invocation_id = await self.repository.create_started(
            request_id=request_id,
            provider=model.provider,
            model=model.model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
        )
        started = perf_counter()
        retry_count = 0
        fallback_used = False

        try:
            result, retry_count = await self._generate_with_retries(
                self._client_for(model_name), request
            )
            if schema:
                result, repair_count = await self._validate_structured(
                    result, schema, self._client_for(model_name), request
                )
                retry_count += repair_count
        except LLMError as primary_error:
            if not self.fallback_model or not primary_error.retryable:
                await self.repository.fail(
                    invocation_id,
                    primary_error,
                    self._elapsed_ms(started),
                    retry_count,
                    fallback_used,
                )
                raise
            fallback = self.model_registry.get(self.fallback_model)
            fallback_used = True
            fallback_request = request.model_copy(update={"model": fallback.model})
            try:
                result, fallback_retries = await self._generate_with_retries(
                    self._client_for(self.fallback_model), fallback_request
                )
                retry_count += fallback_retries
                if schema:
                    result, repair_count = await self._validate_structured(
                        result, schema, self._client_for(self.fallback_model), fallback_request
                    )
                    retry_count += repair_count
            except LLMError as fallback_error:
                await self.repository.fail(
                    invocation_id,
                    fallback_error,
                    self._elapsed_ms(started),
                    retry_count,
                    fallback_used,
                )
                raise

        latency_ms = self._elapsed_ms(started)
        await self.repository.complete(
            invocation_id, result, latency_ms, retry_count, fallback_used
        )
        structured = self._structured_dump(result.text, schema) if schema else None
        return GenerationOutput(
            invocation_id=invocation_id,
            text=result.text,
            structured=structured,
            provider=result.provider,
            model=result.model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            usage=result.usage,
            latency_ms=latency_ms,
            retry_count=retry_count,
            fallback_used=fallback_used,
            finish_reason=result.finish_reason,
        )

    async def stream(
        self, input: GenerationInput, request_id: str
    ) -> AsyncIterator[LLMStreamChunk]:
        output = await self.generate(input, request_id)
        yield LLMStreamChunk(text=output.text)
        yield LLMStreamChunk(finish_reason=output.finish_reason, usage=output.usage)

    async def _generate_with_retries(
        self, client: LLMClient, request: LLMRequest
    ) -> tuple[LLMResult, int]:
        retry_count = 0
        while True:
            try:
                return await client.generate(request), retry_count
            except LLMError as error:
                if not error.retryable or retry_count >= self.max_retries:
                    raise
                retry_count += 1
                await asyncio.sleep(0)

    async def _validate_structured(
        self,
        result: LLMResult,
        schema: type[BaseModel],
        client: LLMClient,
        request: LLMRequest,
    ) -> tuple[LLMResult, int]:
        repair_count = 0
        while True:
            try:
                TypeAdapter(schema).validate_json(result.text)
                return result, repair_count
            except ValueError as error:
                if repair_count >= self.structured_repair_attempts:
                    raise LLMStructuredOutputError("structured_output_invalid") from error
                repair_count += 1
                repair_request = request.model_copy(
                    update={
                        "messages": request.messages
                        + (
                            LLMMessage(
                                role="user", content="Return valid JSON for the requested schema."
                            ),
                        )
                    }
                )
                result = await client.generate(repair_request)

    def _client_for(self, model_name: str) -> LLMClient:
        try:
            return self.clients[model_name]
        except KeyError as error:
            raise KeyError(f"no client configured for model: {model_name}") from error

    @staticmethod
    def _structured_dump(text: str, schema: type[BaseModel]) -> dict[str, object]:
        return TypeAdapter(schema).validate_json(text).model_dump()

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return round((perf_counter() - started) * 1000)
