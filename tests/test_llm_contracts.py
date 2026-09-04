import pytest
from pydantic import ValidationError

from contextwise.application.llm.contracts import LLMMessage, LLMRequest, LLMUsage
from contextwise.application.llm.errors import (
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMTransientError,
)


def test_message_rejects_unknown_role():
    with pytest.raises(ValidationError):
        LLMMessage(role="tool", content="unsupported")


def test_usage_requires_total_to_match_component_tokens():
    with pytest.raises(ValidationError):
        LLMUsage(input_tokens=2, output_tokens=3, total_tokens=4)


def test_request_requires_at_least_one_message():
    with pytest.raises(ValidationError):
        LLMRequest(model="fake-default", messages=())


@pytest.mark.parametrize(
    ("error", "retryable"),
    [
        (LLMTimeoutError("timed out"), True),
        (LLMRateLimitError("rate limited"), True),
        (LLMTransientError("temporary failure"), True),
        (LLMProviderError("invalid request"), False),
    ],
)
def test_error_retryability_is_explicit(error, retryable):
    assert error.retryable is retryable
