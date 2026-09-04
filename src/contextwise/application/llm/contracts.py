from collections.abc import AsyncIterator
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class LLMUsage(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_total_tokens(self) -> "LLMUsage":
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("total_tokens must equal input_tokens plus output_tokens")
        return self


class LLMRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model: str = Field(min_length=1)
    messages: tuple[LLMMessage, ...] = Field(min_length=1)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)
    response_schema: type[BaseModel] | None = None


class LLMResult(BaseModel):
    text: str
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    usage: LLMUsage
    finish_reason: str | None = None


class LLMStreamChunk(BaseModel):
    text: str = ""
    finish_reason: str | None = None
    usage: LLMUsage | None = None


class LLMClient(Protocol):
    async def generate(self, request: LLMRequest) -> LLMResult: ...

    def stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]: ...
