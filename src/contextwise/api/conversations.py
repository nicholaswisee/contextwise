import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from contextwise.api.dependencies import get_assistant_service, require_owner
from contextwise.application.assistant.contracts import (
    AssistantChunkEvent,
    AssistantCompletedEvent,
    AssistantMessageInput,
    ContextInspection,
    Conversation,
    ConversationMessage,
)
from contextwise.application.assistant.errors import (
    ActiveRequestError,
    AssistantError,
    ContextBudgetExceededError,
    ConversationNotFoundError,
    IdempotencyConflictError,
    InvalidAncestryError,
    MessageNotFoundError,
    UnsupportedMessagePartError,
)
from contextwise.application.assistant.service import AssistantService, AssistantStream

router = APIRouter(prefix="/v1", tags=["conversations"])


class ConversationDetail(Conversation):
    messages: tuple[ConversationMessage, ...]


class MessageSendResponse(BaseModel):
    conversation_id: str
    message_id: str
    invocation_id: str
    text: str


@router.post("/conversations", response_model=Conversation)
async def create_conversation(
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> Conversation:
    return await service.create_conversation(owner_id)


@router.get("/conversations", response_model=list[Conversation])
async def list_conversations(
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> list[Conversation]:
    return list(await service.list_conversations(owner_id))


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> ConversationDetail:
    try:
        conversation = await service.get_conversation(conversation_id, owner_id)
        messages = await service.list_messages(conversation_id, owner_id)
        return ConversationDetail(**conversation.model_dump(), messages=messages)
    except AssistantError as error:
        raise _http_error(error) from error


@router.post("/conversations/{conversation_id}/messages", response_model=MessageSendResponse)
async def send_message(
    conversation_id: str,
    input: AssistantMessageInput,
    request: Request,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> MessageSendResponse:
    stream = await _start_message(
        conversation_id, input, request, owner_id, service, idempotency_key
    )
    try:
        events = await stream.collect()
    finally:
        await stream.aclose()
    completed = next(event for event in events if isinstance(event, AssistantCompletedEvent))
    text = "".join(event.text for event in events if isinstance(event, AssistantChunkEvent))
    return MessageSendResponse(
        conversation_id=completed.conversation_id,
        message_id=completed.message_id,
        invocation_id=completed.invocation_id,
        text=text,
    )


@router.post("/conversations/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: str,
    input: AssistantMessageInput,
    request: Request,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> StreamingResponse:
    stream = await _start_message(
        conversation_id, input, request, owner_id, service, idempotency_key
    )
    return _stream_response(stream, request)


@router.post("/messages/{assistant_message_id}/regenerate/stream")
async def regenerate_message(
    assistant_message_id: str,
    request: Request,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> StreamingResponse:
    if not idempotency_key:
        raise HTTPException(status_code=422, detail="Idempotency-Key header is required")
    try:
        stream = await service.regenerate(
            assistant_message_id,
            owner_id,
            idempotency_key,
            request.state.request_id,
        )
    except AssistantError as error:
        raise _http_error(error) from error
    return _stream_response(stream, request)


@router.post("/messages/{message_id}/branch", response_model=Conversation)
async def branch_message(
    message_id: str,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> Conversation:
    try:
        return await service.branch(message_id, owner_id)
    except AssistantError as error:
        raise _http_error(error) from error


@router.get(
    "/conversations/{conversation_id}/context/{message_id}", response_model=ContextInspection
)
async def inspect_context(
    conversation_id: str,
    message_id: str,
    owner_id: Annotated[str, Depends(require_owner)],
    service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> ContextInspection:
    try:
        return await service.inspect_context(conversation_id, message_id, owner_id)
    except AssistantError as error:
        raise _http_error(error) from error


async def _start_message(
    conversation_id: str,
    input: AssistantMessageInput,
    request: Request,
    owner_id: str,
    service: AssistantService,
    idempotency_key: str | None,
) -> AssistantStream:
    if not idempotency_key:
        raise HTTPException(status_code=422, detail="Idempotency-Key header is required")
    try:
        return await service.send_message(
            input,
            owner_id,
            request.state.request_id,
            idempotency_key,
            conversation_id,
        )
    except AssistantError as error:
        raise _http_error(error) from error
    except KeyError as error:
        raise HTTPException(status_code=422, detail=str(error).strip("'")) from error


def _stream_response(stream: AssistantStream, request: Request) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        try:
            async for event in stream:
                yield f"data: {json.dumps(event.model_dump(mode='json'))}\n\n"
                if await request.is_disconnected():
                    break
        except asyncio.CancelledError:
            raise
        finally:
            await stream.aclose()

    return StreamingResponse(events(), media_type="text/event-stream")


def _http_error(error: AssistantError) -> HTTPException:
    if isinstance(error, (ConversationNotFoundError, MessageNotFoundError)):
        return HTTPException(status_code=404, detail=error.code)
    if isinstance(error, ActiveRequestError):
        return HTTPException(status_code=409, detail=error.code)
    if isinstance(
        error,
        (
            IdempotencyConflictError,
            InvalidAncestryError,
            UnsupportedMessagePartError,
            ContextBudgetExceededError,
        ),
    ):
        return HTTPException(status_code=422, detail=error.code)
    return HTTPException(status_code=500, detail="assistant_error")
