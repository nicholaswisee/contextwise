from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from contextwise.application.assistant.contracts import (
    AssistantMessageInput,
    ConversationMessage,
    ImageReferencePart,
    TextPart,
)


def message(
    message_id: str = "message-1",
    *,
    role: str = "user",
    parts: tuple[TextPart | ImageReferencePart, ...] = (TextPart(text="hello"),),
    status: str = "completed",
) -> ConversationMessage:
    now = datetime.now(UTC)
    return ConversationMessage(
        id=message_id,
        conversation_id="conversation-1",
        parent_id=None,
        role=role,
        parts=parts,
        status=status,
        created_at=now,
        updated_at=now,
    )


def test_message_parts_are_discriminated_and_immutable() -> None:
    input_message = AssistantMessageInput(
        parts=[{"type": "text", "text": "hello"}, {"type": "image_ref", "ref": "img-1"}]
    )

    assert isinstance(input_message.parts[0], TextPart)
    assert isinstance(input_message.parts[1], ImageReferencePart)
    with pytest.raises(ValidationError):
        input_message.parts += (TextPart(text="later"),)


def test_conversation_message_rejects_invalid_role() -> None:
    with pytest.raises(ValidationError):
        message(role="system")
