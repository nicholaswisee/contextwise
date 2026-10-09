from math import ceil

from contextwise.application.assistant.contracts import (
    BuiltContext,
    ConversationMessage,
    TextPart,
)
from contextwise.application.assistant.errors import (
    ContextBudgetExceededError,
    UnsupportedMessagePartError,
)
from contextwise.application.llm.contracts import LLMMessage


def estimate_tokens(text: str) -> int:
    """Estimate tokens deterministically as four UTF-8-independent characters per token."""

    return ceil(len(text) / 4)


class ContextBuilder:
    """Build the retained system-plus-conversation context without I/O."""

    def build(
        self,
        system_prompt: str,
        ancestry: tuple[ConversationMessage, ...],
        token_budget: int,
        output_reserve: int,
    ) -> BuiltContext:
        if token_budget <= 0 or output_reserve < 0:
            raise ValueError("token_budget must be positive and output_reserve cannot be negative")

        system_message = LLMMessage(role="system", content=system_prompt)
        system_tokens = estimate_tokens(system_prompt)
        if system_tokens + output_reserve > token_budget:
            raise ContextBudgetExceededError("system prompt exceeds the context budget")

        retained = [
            message
            for message in ancestry
            if message.status not in {"failed", "cancelled", "streaming"}
        ]
        rendered = [self._render_message(message) for message in retained]
        estimated = system_tokens + sum(estimate_tokens(message.content) for message in rendered)
        while rendered and estimated + output_reserve > token_budget:
            removed = rendered.pop(0)
            estimated -= estimate_tokens(removed.content)

        truncated = len(rendered) < len(retained)
        return BuiltContext(
            messages=(system_message, *rendered),
            selected_message_ids=tuple(message.id for message in retained[-len(rendered) :])
            if rendered
            else (),
            estimated_input_tokens=estimated,
            truncated=truncated,
        )

    @staticmethod
    def _render_message(message: ConversationMessage) -> LLMMessage:
        text_parts: list[str] = []
        for part in message.parts:
            if not isinstance(part, TextPart):
                raise UnsupportedMessagePartError(
                    "image and file references are stored but not supported by the text model"
                )
            text_parts.append(part.text)
        return LLMMessage(role=message.role, content="\n".join(text_parts))
