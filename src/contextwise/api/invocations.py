from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from contextwise.api.dependencies import get_invocation_repository
from contextwise.infrastructure.invocations import InvocationRepository

router = APIRouter(prefix="/v1/invocations", tags=["invocations"])


class InvocationResponse(BaseModel):
    id: str
    request_id: str
    provider: str
    model: str
    status: str
    prompt_name: str | None
    prompt_version: int | None
    started_at: datetime
    completed_at: datetime | None
    latency_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    finish_reason: str | None
    retry_count: int
    fallback_used: bool
    error_code: str | None


@router.get("/{invocation_id}", response_model=InvocationResponse)
async def get_invocation(
    invocation_id: str,
    repository: Annotated[InvocationRepository, Depends(get_invocation_repository)],
) -> InvocationResponse:
    invocation = await repository.get(invocation_id)
    if invocation is None:
        raise HTTPException(status_code=404, detail="invocation not found")
    return InvocationResponse(
        id=invocation.id,
        request_id=invocation.request_id,
        provider=invocation.provider,
        model=invocation.model,
        status=invocation.status,
        prompt_name=invocation.prompt_name,
        prompt_version=invocation.prompt_version,
        started_at=invocation.started_at,
        completed_at=invocation.completed_at,
        latency_ms=invocation.latency_ms,
        input_tokens=invocation.input_tokens,
        output_tokens=invocation.output_tokens,
        total_tokens=invocation.total_tokens,
        finish_reason=invocation.finish_reason,
        retry_count=invocation.retry_count,
        fallback_used=invocation.fallback_used,
        error_code=invocation.error_code,
    )
