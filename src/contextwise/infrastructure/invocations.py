from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from contextwise.application.llm.contracts import LLMResult
from contextwise.application.llm.errors import LLMError
from contextwise.infrastructure.models import ModelInvocation


class InvocationRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create_started(
        self,
        request_id: str,
        provider: str,
        model: str,
        prompt_name: str | None,
        prompt_version: int | None,
    ) -> str:
        invocation = ModelInvocation(
            id=str(uuid4()),
            request_id=request_id,
            provider=provider,
            model=model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            status="started",
        )
        async with self.session_factory.begin() as session:
            session.add(invocation)
        return invocation.id

    async def complete(
        self,
        invocation_id: str,
        result: LLMResult,
        latency_ms: int,
        retry_count: int,
        fallback_used: bool,
    ) -> None:
        async with self.session_factory.begin() as session:
            invocation = await self._get_required(session, invocation_id)
            invocation.status = "completed"
            invocation.completed_at = datetime.now(UTC)
            invocation.latency_ms = latency_ms
            invocation.input_tokens = result.usage.input_tokens
            invocation.output_tokens = result.usage.output_tokens
            invocation.total_tokens = result.usage.total_tokens
            invocation.finish_reason = result.finish_reason
            invocation.retry_count = retry_count
            invocation.fallback_used = fallback_used

    async def fail(
        self,
        invocation_id: str,
        error: LLMError,
        latency_ms: int,
        retry_count: int,
        fallback_used: bool,
    ) -> None:
        async with self.session_factory.begin() as session:
            invocation = await self._get_required(session, invocation_id)
            invocation.status = "failed"
            invocation.completed_at = datetime.now(UTC)
            invocation.latency_ms = latency_ms
            invocation.retry_count = retry_count
            invocation.fallback_used = fallback_used
            invocation.error_code = error.code
            invocation.error_message = error.code

    async def cancel(self, invocation_id: str, latency_ms: int) -> None:
        async with self.session_factory.begin() as session:
            invocation = await self._get_required(session, invocation_id)
            invocation.status = "cancelled"
            invocation.completed_at = datetime.now(UTC)
            invocation.latency_ms = latency_ms

    async def get(self, invocation_id: str) -> ModelInvocation | None:
        async with self.session_factory() as session:
            return await session.get(ModelInvocation, invocation_id)

    @staticmethod
    async def _get_required(session: AsyncSession, invocation_id: str) -> ModelInvocation:
        invocation = await session.get(ModelInvocation, invocation_id)
        if invocation is None:
            raise KeyError(f"unknown invocation: {invocation_id}")
        return invocation
