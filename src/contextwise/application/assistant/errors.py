class AssistantError(Exception):
    code = "assistant_error"


class ConversationNotFoundError(AssistantError):
    code = "conversation_not_found"


class MessageNotFoundError(AssistantError):
    code = "message_not_found"


class ActiveRequestError(AssistantError):
    code = "active_request"


class IdempotencyConflictError(AssistantError):
    code = "idempotency_conflict"


class InvalidAncestryError(AssistantError):
    code = "invalid_ancestry"


class UnsupportedMessagePartError(AssistantError):
    code = "unsupported_message_part"


class ContextBudgetExceededError(AssistantError):
    code = "context_budget_exceeded"
