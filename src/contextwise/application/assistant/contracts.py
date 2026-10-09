from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from contextwise.application.llm.contracts import LLMMessage


class TextPart(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["text"] = "text"
    text: str = Field(min_length=1)


class ImageReferencePart(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["image_ref"] = "image_ref"
    ref: str = Field(min_length=1)


class FileReferencePart(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["file_ref"] = "file_ref"
    ref: str = Field(min_length=1)


MessagePart = Annotated[
    TextPart | ImageReferencePart | FileReferencePart,
    Field(discriminator="type"),
]


class ConversationMessage(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: str = Field(min_length=1)
    conversation_id: str = Field(min_length=1)
    parent_id: str | None = None
    role: Literal["user", "assistant"]
    parts: tuple[MessagePart, ...] = ()
    status: Literal["streaming", "completed", "failed", "cancelled"]
    model: str | None = None
    model_name: str | None = None
    provider: str | None = None
    prompt_name: str | None = None
    prompt_version: int | None = None
    request_settings: dict[str, object] | None = None
    invocation_id: str | None = None
    source_conversation_id: str | None = None
    source_message_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Conversation(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: str = Field(min_length=1)
    owner_id: str = Field(min_length=1)
    title: str | None = None
    head_message_id: str | None = None
    source_conversation_id: str | None = None
    source_message_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AssistantMessageInput(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    conversation_id: str | None = Field(default=None, min_length=1)
    parts: tuple[MessagePart, ...] = Field(min_length=1)
    model: str | None = Field(default=None, min_length=1)
    prompt_version: int | None = Field(default=None, gt=0)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)


class BuiltContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    messages: tuple[LLMMessage, ...] = Field(min_length=1)
    selected_message_ids: tuple[str, ...]
    estimated_input_tokens: int = Field(ge=0)
    truncated: bool


class ContextSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    prompt_name: str = Field(min_length=1)
    prompt_version: int = Field(gt=0)
    model_name: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    temperature: float | None = None
    max_tokens: int | None = None
    provider_messages: tuple[LLMMessage, ...] = Field(min_length=1)
    selected_message_ids: tuple[str, ...]
    estimated_input_tokens: int = Field(ge=0)
    truncated: bool


class ContextInspection(BaseModel):
    model_config = ConfigDict(frozen=True)

    conversation_id: str
    message_id: str
    invocation_id: str
    snapshot: ContextSnapshot


class AssistantChunkEvent(BaseModel):
    type: Literal["chunk"] = "chunk"
    text: str


class AssistantCompletedEvent(BaseModel):
    type: Literal["completed"] = "completed"
    conversation_id: str
    message_id: str
    invocation_id: str


class AssistantErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    code: str
    conversation_id: str
    message_id: str
    invocation_id: str | None = None


AssistantEvent = Annotated[
    AssistantChunkEvent | AssistantCompletedEvent | AssistantErrorEvent,
    Field(discriminator="type"),
]
