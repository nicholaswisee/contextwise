class LLMError(Exception):
    code = "provider_error"
    retryable = False


class LLMTimeoutError(LLMError):
    code = "timeout"
    retryable = True


class LLMRateLimitError(LLMError):
    code = "rate_limited"
    retryable = True


class LLMTransientError(LLMError):
    code = "transient_error"
    retryable = True


class LLMProviderError(LLMError):
    code = "provider_error"


class LLMStructuredOutputError(LLMError):
    code = "structured_output_invalid"
