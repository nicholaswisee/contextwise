from datetime import UTC, datetime

import pytest

from contextwise.application.assistant.contracts import (
    AssistantMessageInput,
    Conversation,
    ConversationMessage,
    TextPart,
)
from contextwise.application.assistant.service import AssistantService
from contextwise.application.llm.errors import LLMTimeoutError
from contextwise.application.llm.fake_client import FakeLLMClient
from contextwise.application.llm.generation_service import GenerationService
from contextwise.application.llm.model_registry import ModelRegistry
from contextwise.application.llm.prompt_registry import PromptRegistry
from contextwise.application.llm.schema_registry import SchemaRegistry
from contextwise.config import Settings


def now() -> datetime:
    return datetime.now(UTC)


class FakeInvocationRepository:
    def __init__(self) -> None:
        self.started: list[dict[str, object]] = []
        self.completed: list[str] = []
        self.failed: list[str] = []
        self.cancelled: list[str] = []

    async def create_started(self, **kwargs: object) -> str:
        self.started.append(kwargs)
        return f"invocation-{len(self.started)}"

    async def complete(
        self, invocation_id, result, latency_ms, retry_count, fallback_used, estimated_cost_usd
    ):
        self.completed.append(invocation_id)

    async def fail(self, invocation_id, error, latency_ms, retry_count, fallback_used):
        self.failed.append(invocation_id)

    async def cancel(self, invocation_id, latency_ms):
        self.cancelled.append(invocation_id)


class FakeConversationRepository:
    def __init__(self) -> None:
        self.conversation = Conversation(id="conversation-1", owner_id="local")
        self.messages: dict[str, ConversationMessage] = {}
        self.claims: dict[str, dict[str, str | None]] = {}
        self.assistant_calls = 0

    async def get_owned(self, conversation_id, owner_id):
        if conversation_id == self.conversation.id and owner_id == self.conversation.owner_id:
            return self.conversation
        return None

    async def claim_generation(self, conversation_id, key, fingerprint, owner_id, parts, **kwargs):
        if key in self.claims:
            claim = self.claims[key]
            claim.replay = True
            return claim
        user_id = f"user-{len(self.claims) + 1}"
        assistant_id = f"assistant-{len(self.claims) + 1}"
        user = ConversationMessage(
            id=user_id,
            conversation_id=conversation_id,
            role="user",
            parts=tuple(parts),
            status="completed",
            created_at=now(),
            updated_at=now(),
        )
        assistant = ConversationMessage(
            id=assistant_id,
            conversation_id=conversation_id,
            parent_id=user_id,
            role="assistant",
            parts=(),
            status="streaming",
            created_at=now(),
            updated_at=now(),
        )
        self.messages[user_id] = user
        self.messages[assistant_id] = assistant
        self.assistant_calls += 1
        claim = type(
            "Claim",
            (),
            {
                "request_id": f"request-{len(self.claims) + 1}",
                "conversation_id": conversation_id,
                "user_message_id": user_id,
                "assistant_message_id": assistant_id,
                "invocation_id": None,
                "status": "streaming",
                "replay": False,
                "request_fingerprint": fingerprint,
                "error_code": None,
            },
        )()
        self.claims[key] = claim
        return claim

    async def claim_regeneration(self, assistant_message_id, key, fingerprint, owner_id, **kwargs):
        original = self.messages[assistant_message_id]
        parent_id = original.parent_id
        assistant_id = f"assistant-{len(self.messages) + 1}"
        assistant = original.model_copy(
            update={"id": assistant_id, "parts": (), "status": "streaming", "updated_at": now()}
        )
        self.messages[assistant_id] = assistant
        self.assistant_calls += 1
        claim = type(
            "Claim",
            (),
            {
                "request_id": f"request-{len(self.claims) + 1}",
                "conversation_id": original.conversation_id,
                "user_message_id": parent_id,
                "assistant_message_id": assistant_id,
                "invocation_id": None,
                "status": "streaming",
                "replay": False,
                "request_fingerprint": fingerprint,
                "error_code": None,
            },
        )()
        self.claims[key] = claim
        return claim

    async def get_ancestry(self, message_id, owner_id):
        return (self.messages[message_id],)

    async def attach_invocation(self, request_id, owner_id, invocation_id):
        return None

    async def append_assistant_text(self, message_id, text, owner_id):
        message = self.messages[message_id]
        text_part = TextPart(
            text="".join(part.text for part in message.parts if isinstance(part, TextPart)) + text
        )
        self.messages[message_id] = message.model_copy(update={"parts": (text_part,)})

    async def mark_terminal(self, request_id, status, owner_id, error_code=None):
        claim = next(claim for claim in self.claims.values() if claim.request_id == request_id)
        message = self.messages[claim.assistant_message_id]
        self.messages[message.id] = message.model_copy(update={"status": status})
        claim.status = status
        claim.error_code = error_code

    async def get_request(self, conversation_id, key, owner_id):
        return self.claims.get(key)

    async def get_request_for_message(self, message_id, owner_id):
        return next(
            (claim for claim in self.claims.values() if claim.assistant_message_id == message_id),
            None,
        )

    async def get_message(self, message_id, owner_id):
        return self.messages.get(message_id)

    async def copy_ancestry(self, conversation_id, message_id, owner_id):
        return Conversation(id="branch-1", owner_id=owner_id, head_message_id=message_id)

    async def update_title(self, conversation_id, owner_id, title):
        return None

    async def count_assistant_messages(self, conversation_id, owner_id):
        return len([message for message in self.messages.values() if message.role == "assistant"])


def service(client: FakeLLMClient, repository: FakeConversationRepository) -> AssistantService:
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost/contextwise",
        llm_max_retries=0,
    )
    invocation_repository = FakeInvocationRepository()
    generation = GenerationService(
        model_registry=ModelRegistry.from_settings(settings),
        prompt_registry=PromptRegistry(),
        schema_registry=SchemaRegistry(),
        clients={"fake-default": client},
        repository=invocation_repository,
        max_retries=0,
        structured_repair_attempts=0,
        fallback_model=None,
    )
    return AssistantService(
        repository=repository,
        invocation_repository=invocation_repository,
        generation_service=generation,
        prompt_registry=PromptRegistry(),
        model_registry=ModelRegistry.from_settings(settings),
        context_budget=4096,
        output_reserve=512,
    )


@pytest.mark.asyncio
async def test_regeneration_creates_a_sibling_and_preserves_original() -> None:
    repository = FakeConversationRepository()
    assistant = service(FakeLLMClient(text="answer"), repository)
    input_message = AssistantMessageInput(
        conversation_id="conversation-1", parts=(TextPart(text="hello"),)
    )

    original_stream = await assistant.send_message(input_message, "local", "request-1", "key-1")
    original_events = await original_stream.collect()
    original_id = original_events[-1].message_id
    original = await repository.get_message(original_id, "local")

    regenerated_stream = await assistant.regenerate(original_id, "local", "key-2", "request-2")
    regenerated_events = await regenerated_stream.collect()

    assert regenerated_events[-1].message_id != original_id
    assert await repository.get_message(original_id, "local") == original


@pytest.mark.asyncio
async def test_stream_failure_marks_existing_placeholder_failed_without_duplicate() -> None:
    repository = FakeConversationRepository()
    assistant = service(
        FakeLLMClient(stream_chunks=("partial",), stream_failure=LLMTimeoutError("timed out")),
        repository,
    )

    stream = await assistant.send_message(
        AssistantMessageInput(conversation_id="conversation-1", parts=(TextPart(text="hello"),)),
        "local",
        "request-3",
        "key-3",
    )
    events = await stream.collect()

    assert events[-1].type == "error"
    assert await repository.count_assistant_messages("conversation-1", "local") == 1
    assert repository.messages[events[-1].message_id].status == "failed"


@pytest.mark.asyncio
async def test_completed_key_replays_without_another_provider_call() -> None:
    repository = FakeConversationRepository()
    client = FakeLLMClient(text="answer")
    assistant = service(client, repository)
    input_message = AssistantMessageInput(
        conversation_id="conversation-1", parts=(TextPart(text="hello"),)
    )

    first = await assistant.send_message(input_message, "local", "request-1", "key-1")
    await first.collect()
    second = await assistant.send_message(input_message, "local", "request-2", "key-1")
    events = await second.collect()

    assert events[-1].type == "completed"
    assert len(client.calls) == 1
