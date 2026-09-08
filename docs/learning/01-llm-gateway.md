# Milestone 1 — LLM Gateway Learning Note

## What was built

Contextwise now has a provider-neutral `LLMClient` boundary, deterministic fake client, LiteLLM adapter, model/prompt/schema registries, persisted invocation records, retry/fallback handling, structured output validation, generation APIs, and SSE streaming.

## What worked

- The fake provider made retries, fallback, invalid structured output, streaming cancellation, and partial stream failures deterministic.
- Application services import Contextwise contracts rather than LiteLLM types.
- Invocation records store lifecycle metadata without prompts, raw responses, or provider credentials.
- The `answer` schema validates returned JSON before the API returns structured data.

## What was hard

- SQLAlchemy's typed `DeclarativeBase` was needed once the first mapped model was added; the earlier `declarative_base()` was too imprecise for strict mypy.
- HTTP streaming needs its own lifecycle path; generating a full response before emitting SSE does not test upstream cancellation or client disconnect cleanup.
- LiteLLM adapter tests must patch the local adapter boundary, not use real credentials.

## Open questions

- A real provider comparison is pending explicit credentials.
- Structured streaming is intentionally rejected until it can validate the final response.
- Streaming fallback policy is intentionally not implemented; fallback occurs before a stream begins.
- Cost estimates are persisted as `0` for fake results until provider-specific pricing reconciliation is added.
- The provider comparison runner belongs at the experiment composition boundary so the application layer remains independent of LiteLLM.
- A comparison artifact can safely record requested and returned model metadata, token counts, latency, and validation status without recording prompts, responses, or credentials.
