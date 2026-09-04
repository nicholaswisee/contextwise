from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from contextwise.api.dependencies import get_model_registry, get_prompt_registry
from contextwise.application.llm.model_registry import ModelRegistry
from contextwise.application.llm.prompt_registry import PromptRegistry

router = APIRouter(prefix="/v1", tags=["llm-registry"])


class ModelResponse(BaseModel):
    name: str
    provider: str
    model: str
    capabilities: tuple[str, ...]


class PromptResponse(BaseModel):
    name: str
    version: int


@router.get("/models", response_model=list[ModelResponse])
async def list_models(
    registry: Annotated[ModelRegistry, Depends(get_model_registry)],
) -> list[ModelResponse]:
    return [
        ModelResponse(
            name=model.name,
            provider=model.provider,
            model=model.model,
            capabilities=tuple(sorted(model.capabilities)),
        )
        for model in registry.list()
    ]


@router.get("/prompts", response_model=list[PromptResponse])
async def list_prompts(
    registry: Annotated[PromptRegistry, Depends(get_prompt_registry)],
) -> list[PromptResponse]:
    return [PromptResponse(name=prompt.name, version=prompt.version) for prompt in registry.list()]
