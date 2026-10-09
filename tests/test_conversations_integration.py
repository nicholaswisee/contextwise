import pytest

from contextwise.application.assistant.contracts import TextPart
from contextwise.config import Settings
from contextwise.infrastructure.conversations import ConversationRepository
from contextwise.infrastructure.database import Database

pytestmark = pytest.mark.integration


@pytest.fixture
def repository(monkeypatch, apply_migrations):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://contextwise:contextwise@localhost:5434/contextwise_test",
    )
    database = Database(Settings())
    return ConversationRepository(database.session_factory)


@pytest.mark.asyncio
async def test_branch_copies_ancestry_and_keeps_future_messages_independent(repository) -> None:
    source = await repository.create_conversation("local")
    user = await repository.create_message(
        source.id,
        parent_id=None,
        role="user",
        parts=(TextPart(text="first"),),
        owner_id="local",
    )
    fork_message = await repository.create_message(
        source.id,
        parent_id=user.id,
        role="assistant",
        parts=(TextPart(text="answer"),),
        owner_id="local",
        status="completed",
    )

    branch = await repository.copy_ancestry(source.id, fork_message.id, owner_id="local")
    branch_head = branch.head_message_id
    assert branch_head is not None
    await repository.create_message(
        branch.id,
        parent_id=branch_head,
        role="user",
        parts=(TextPart(text="branch only"),),
        owner_id="local",
    )

    source_messages = await repository.list_messages(source.id, "local")
    branch_messages = await repository.list_messages(branch.id, "local")

    assert len(source_messages) == 2
    assert len(branch_messages) == 3
    assert branch_messages[0].source_message_id == user.id
    assert branch_messages[1].source_message_id == fork_message.id


@pytest.mark.asyncio
async def test_claim_generation_is_unique_per_conversation_key(repository) -> None:
    conversation = await repository.create_conversation("local")

    first = await repository.claim_generation(
        conversation.id,
        "key-1",
        "fingerprint",
        "local",
        (TextPart(text="hello"),),
    )
    second = await repository.claim_generation(
        conversation.id,
        "key-1",
        "fingerprint",
        "local",
        (TextPart(text="hello"),),
    )

    assert second.request_id == first.request_id
    assert second.assistant_message_id == first.assistant_message_id
