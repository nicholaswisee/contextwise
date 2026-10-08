from datetime import UTC, datetime

import pytest

from contextwise.application.assistant.context_builder import ContextBuilder
from contextwise.application.assistant.contracts import ConversationMessage, TextPart
from contextwise.application.assistant.errors import UnsupportedMessagePartError


def make_message(
    message_id: str,
    role: str,
    text: str,
    *,
    status: str = "completed",
    parent_id: str | None = None,
) -> ConversationMessage:
    now = datetime.now(UTC)
    return ConversationMessage(
        id=message_id,
        conversation_id="conversation-1",
        parent_id=parent_id,
        role=role,
        parts=(TextPart(text=text),),
        status=status,
        created_at=now,
        updated_at=now,
    )


def test_context_builder_keeps_newest_complete_ancestry_within_budget() -> None:
    old_message = make_message("old", "user", "old " * 8)
    newest_message = make_message("newest", "assistant", "newest")

    result = ContextBuilder().build(
        system_prompt="System rules.",
        ancestry=(old_message, newest_message),
        token_budget=12,
        output_reserve=4,
    )

    assert result.selected_message_ids == (newest_message.id,)
    assert result.messages[0].role == "system"
    assert result.truncated is True


def test_context_builder_rejects_non_text_parts() -> None:
    from contextwise.application.assistant.contracts import ImageReferencePart

    image_message = make_message("image", "user", "placeholder").model_copy(
        update={"parts": (ImageReferencePart(ref="image-1"),)}
    )

    with pytest.raises(UnsupportedMessagePartError):
        ContextBuilder().build("System rules.", (image_message,), 100, 10)


def test_context_builder_excludes_terminal_failed_and_streaming_assistants() -> None:
    messages = (
        make_message("user", "user", "keep me"),
        make_message("failed", "assistant", "do not keep", status="failed"),
        make_message("streaming", "assistant", "do not keep", status="streaming"),
        make_message("cancelled", "assistant", "do not keep", status="cancelled"),
    )

    result = ContextBuilder().build("System rules.", messages, 100, 10)

    assert result.selected_message_ids == ("user",)
