import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from contextwise.api.dependencies import get_generation_service
from contextwise.application.llm.errors import LLMError
from contextwise.application.llm.generation_service import (
    GenerationInput,
    GenerationOutput,
    GenerationService,
)

router = APIRouter(prefix="/v1/generations", tags=["generations"])


@router.post("", response_model=GenerationOutput)
async def generate(
    input: GenerationInput,
    request: Request,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationOutput:
    try:
        return await service.generate(input, request.state.request_id)
    except KeyError as error:
        raise HTTPException(status_code=422, detail=str(error).strip("'")) from error
    except LLMError as error:
        raise HTTPException(status_code=502, detail=error.code) from error


@router.post("/stream")
async def stream(
    input: GenerationInput,
    request: Request,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> StreamingResponse:
    if input.response_schema:
        raise HTTPException(status_code=422, detail="structured streaming is not supported")

    async def events() -> AsyncIterator[str]:
        stream = service.stream(input, request.state.request_id)
        try:
            async for chunk in stream:
                if await request.is_disconnected():
                    break
                if chunk.invocation_id:
                    payload = {"type": "completed", "invocation_id": chunk.invocation_id}
                else:
                    payload = {"type": "chunk", "text": chunk.text}
                yield f"data: {json.dumps(payload)}\n\n"
        except asyncio.CancelledError:
            raise
        except LLMError as error:
            yield f"data: {json.dumps({'type': 'error', 'code': error.code})}\n\n"
        finally:
            await stream.aclose()

    return StreamingResponse(events(), media_type="text/event-stream")
