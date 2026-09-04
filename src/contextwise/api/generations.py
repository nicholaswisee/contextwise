from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

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
