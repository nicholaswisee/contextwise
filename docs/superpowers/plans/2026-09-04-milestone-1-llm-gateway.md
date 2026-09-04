# Milestone 1 LLM Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task in the current session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a provider-neutral, typed LLM generation vertical slice with deterministic fake-provider coverage, an opt-in LiteLLM adapter, persisted invocation history, retry/fallback policy, and SSE streaming.

**Architecture:** Application code will depend on a small `LLMClient` protocol and Contextwise-owned value models, never on LiteLLM types. A fake client will be the first complete adapter and the default local model; the LiteLLM adapter will translate between the internal contracts and provider responses at the infrastructure boundary. Generation requests will flow through a service that resolves model and prompt versions, owns retry/fallback decisions, validates registered Pydantic response schemas, and persists invocation state through a repository.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy asyncio, PostgreSQL, Alembic, LiteLLM, pytest, pytest-asyncio, Ruff, mypy, and standard-library `asyncio` retry/cancellation primitives.

## Global Constraints

- Keep external provider SDK types behind `src/contextwise/infrastructure/llm/`.
- Keep API handlers responsible for transport validation only; generation orchestration belongs in the application layer.
- Use the fake adapter for deterministic local tests and as the default configuration when no provider key is configured.
- Do not add a retry library; implement the bounded policy with `asyncio` and typed internal errors.
- Retry only timeout, rate-limit, and explicitly transient provider failures.
- Allow fallback only when a configured fallback model exists and disclose it in the API response and persisted invocation.
- Never persist provider credentials or raw provider responses.
- Validate structured output with a registered Pydantic model before returning it to the caller.
- Keep streamed SSE events JSON-encoded and terminate every successful stream with a final event.
- Do not claim a probabilistic quality result from the fake adapter; the baseline must label deterministic and real-provider results separately.
- Release tagging is not required for this project.

## File Map

### New application files

- `src/contextwise/application/llm/contracts.py`: provider-neutral messages, requests, usage, results, chunks, and client protocol.
- `src/contextwise/application/llm/errors.py`: typed timeout, rate-limit, transient, provider, and structured-output errors.
- `src/contextwise/application/llm/fake_client.py`: deterministic fake generation and streaming adapter used by tests and local development.
- `src/contextwise/application/llm/model_registry.py`: configured model definitions and capability lookup.
- `src/contextwise/application/llm/prompt_registry.py`: versioned prompt definitions and rendering.
- `src/contextwise/application/llm/schema_registry.py`: named Pydantic response schemas supported by the HTTP API.
- `src/contextwise/application/llm/generation_service.py`: model/prompt resolution, retry/fallback, structured validation, streaming coordination, and invocation updates.

### New infrastructure files

- `src/contextwise/infrastructure/llm/litellm_client.py`: LiteLLM-to-Contextwise adapter.
- `src/contextwise/infrastructure/invocations.py`: SQLAlchemy repository for invocation lifecycle records.
- `src/contextwise/infrastructure/models.py`: SQLAlchemy `ModelInvocation` table model.
- `src/contextwise/infrastructure/migrations/versions/0002_model_invocations.py`: schema migration.

### New API files

- `src/contextwise/api/generations.py`: free-form and structured generation endpoints, including SSE streaming.
- `src/contextwise/api/llm_registry.py`: model and prompt registry endpoints.
- `src/contextwise/api/invocations.py`: invocation inspection endpoint.

### Existing files to modify

- `pyproject.toml`: add LiteLLM as the only new runtime provider dependency.
- `src/contextwise/config/settings.py`: add model, provider, timeout, retry, fallback, and API-key configuration.
- `src/contextwise/api/dependencies.py`: construct the registries, clients, repository, and generation service in `AppState`.
- `src/contextwise/api/main.py`: register the new routers and close any new resources during lifespan shutdown.
- `src/contextwise/infrastructure/database.py`: import model metadata before Alembic reads `Base.metadata`.
- `src/contextwise/infrastructure/migrations/env.py`: ensure model metadata is imported for migration autogeneration.
- `tests/conftest.py`: add service fixtures using fake clients and isolated repositories.
- `docs/milestones/01-llm-gateway-typed-generation.md`: check off only verified work and record remaining evidence.

### New test and evidence files

- `tests/test_llm_contracts.py`
- `tests/test_fake_llm_client.py`
- `tests/test_generation_service.py`
- `tests/test_generations.py`
- `tests/test_llm_registry.py`
- `tests/test_invocations_integration.py`
- `tests/test_litellm_client.py`
- `tests/test_llm_logging.py`
- `experiments/provider-baseline-001/prompts.jsonl`
- `experiments/provider-baseline-001/run.py`
- `experiments/provider-baseline-001/README.md`
- `docs/learning/01-llm-gateway.md`
- `docs/RELEASE_NOTES/0.1.0.md`

---

### Task 1: Add provider-neutral contracts and typed errors

**Files:**
- Create: `src/contextwise/application/llm/contracts.py`
- Create: `src/contextwise/application/llm/errors.py`
- Create: `tests/test_llm_contracts.py`

**Interfaces:**
- `LLMMessage(role: Literal["system", "user", "assistant"], content: str)`
- `LLMUsage(input_tokens: int, output_tokens: int, total_tokens: int)`
- `LLMRequest(model: str, messages: tuple[LLMMessage, ...], temperature: float | None, max_tokens: int | None, response_schema: type[BaseModel] | None)`
- `LLMResult(text: str, provider: str, model: str, usage: LLMUsage, finish_reason: str | None)`
- `LLMStreamChunk(text: str, finish_reason: str | None, usage: LLMUsage | None)`
- `LLMClient.generate(request: LLMRequest) -> Awaitable[LLMResult]`
- `LLMClient.stream(request: LLMRequest) -> AsyncIterator[LLMStreamChunk]`
- `LLMError(code: str, retryable: bool)` with concrete timeout, rate-limit, transient-provider, provider, and structured-output subclasses.

- [ ] **Step 1: Write tests for contract construction and error classification.** Assert message roles are validated, usage totals are explicit, and only timeout/rate-limit/transient errors are retryable.
- [ ] **Step 2: Run `uv run pytest tests/test_llm_contracts.py -v`.** Expected: FAIL because the contract module does not exist.
- [ ] **Step 3: Implement the contracts and error classes.** Keep them free of LiteLLM imports and provider-specific fields.
- [ ] **Step 4: Run `uv run pytest tests/test_llm_contracts.py -v`.** Expected: PASS.
- [ ] **Step 5: Run `uv run mypy src/contextwise/application/llm`.** Expected: PASS.

### Task 2: Implement the fake adapter and contract tests

**Files:**
- Create: `src/contextwise/application/llm/fake_client.py`
- Create: `tests/test_fake_llm_client.py`

**Interfaces:**
- `FakeLLMClient(provider: str = "fake", text: str = "Hello from fake provider.", structured_json: str | None = None, stream_chunks: tuple[str, ...] | None = None, failures: tuple[LLMError, ...] = ())`
- `FakeLLMClient.generate(request) -> LLMResult`
- `FakeLLMClient.stream(request) -> AsyncIterator[LLMStreamChunk]`
- `FakeLLMClient.calls: list[LLMRequest]`

- [ ] **Step 1: Write tests for deterministic free-form, structured, streaming, and configured failure behavior.** Assert each call is recorded and fake usage is deterministic.
- [ ] **Step 2: Run `uv run pytest tests/test_fake_llm_client.py -v`.** Expected: FAIL because the adapter does not exist.
- [ ] **Step 3: Implement the fake adapter.** Make configured failures raise the typed errors in order; do not add random behavior or sleeps by default.
- [ ] **Step 4: Run `uv run pytest tests/test_fake_llm_client.py -v`.** Expected: PASS.
- [ ] **Step 5: Add a parametrized contract test that exercises both fake `generate()` and `stream()` against the `LLMClient` protocol.**
- [ ] **Step 6: Run `uv run pytest tests/test_llm_contracts.py tests/test_fake_llm_client.py -v`.** Expected: PASS.

### Task 3: Add settings, model registry, prompt registry, and schema registry

**Files:**
- Modify: `src/contextwise/config/settings.py`
- Create: `src/contextwise/application/llm/model_registry.py`
- Create: `src/contextwise/application/llm/prompt_registry.py`
- Create: `src/contextwise/application/llm/schema_registry.py`
- Create: `tests/test_llm_registry.py`

**Interfaces:**
- `ModelDefinition(name: str, provider: str, model: str, capabilities: frozenset[str])`
- `ModelRegistry.list() -> tuple[ModelDefinition, ...]`
- `ModelRegistry.get(name: str) -> ModelDefinition`
- `PromptDefinition(name: str, version: int, template: str)`
- `PromptRegistry.list() -> tuple[PromptDefinition, ...]`
- `PromptRegistry.render(name: str, version: int | None, prompt: str) -> tuple[str, int]`
- `SchemaRegistry.get(name: str) -> type[BaseModel]`
- Default model: `fake-default`; optional primary/fallback model names come from `LLM_PRIMARY_MODEL` and `LLM_FALLBACK_MODEL`.

- [ ] **Step 1: Add failing tests for default fake model, unknown model/prompt/schema errors, prompt version resolution, and model capability lookup.**
- [ ] **Step 2: Run `uv run pytest tests/test_llm_registry.py -v`.** Expected: FAIL because the registries do not exist.
- [ ] **Step 3: Add typed settings for `LLM_PRIMARY_MODEL`, `LLM_FALLBACK_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES`, `LLM_STRUCTURED_REPAIR_ATTEMPTS`, and `LLM_MODELS_JSON`, with API keys accepted only as provider configuration values.**
- [ ] **Step 4: Implement in-memory registries with one fake text/structured/streaming model and one configured LiteLLM model definition when `LLM_MODELS_JSON` is provided.**
- [ ] **Step 5: Run `uv run pytest tests/test_llm_registry.py -v`.** Expected: PASS.
- [ ] **Step 6: Run `uv run ruff check src tests && uv run mypy src`.** Expected: PASS.

### Task 4: Add the LiteLLM adapter

**Files:**
- Modify: `pyproject.toml`
- Create: `src/contextwise/infrastructure/llm/litellm_client.py`
- Create: `tests/test_litellm_client.py`

**Interfaces:**
- `LiteLLMClient(provider: str, timeout_seconds: float)` implementing `LLMClient`.
- Translate `LLMMessage` to plain `{role, content}` dictionaries.
- Translate LiteLLM response usage and finish reason into `LLMUsage` and `LLMResult`.
- Pass a registered Pydantic model through LiteLLM `response_format` for structured generation.
- Translate LiteLLM timeout, rate-limit, and generic exceptions into internal typed errors without exposing raw provider objects.

- [ ] **Step 1: Add `litellm` to runtime dependencies with a compatible lower bound and run `uv sync`.**
- [ ] **Step 2: Write adapter tests using a patched local boundary function, not real provider credentials.** Assert request translation, response translation, structured `response_format`, stream chunk translation, and exception mapping.
- [ ] **Step 3: Run `uv run pytest tests/test_litellm_client.py -v`.** Expected: FAIL because the adapter does not exist.
- [ ] **Step 4: Implement the adapter using `await acompletion(model=request.model, messages=messages, response_format=request.response_schema, timeout=self.timeout_seconds)` for non-streaming calls and the same call with `stream=True` for streaming.** Keep all LiteLLM imports in this file.
- [ ] **Step 5: Run `uv run pytest tests/test_litellm_client.py -v`.** Expected: PASS.
- [ ] **Step 6: Run `uv run mypy src/contextwise/infrastructure/llm/litellm_client.py`.** Expected: PASS.

### Task 5: Add invocation persistence and repository operations

**Files:**
- Modify: `src/contextwise/infrastructure/database.py`
- Modify: `src/contextwise/infrastructure/migrations/env.py`
- Create: `src/contextwise/infrastructure/models.py`
- Create: `src/contextwise/infrastructure/invocations.py`
- Create: `src/contextwise/infrastructure/migrations/versions/0002_model_invocations.py`
- Create: `tests/test_invocations_integration.py`

**Interfaces:**
- `InvocationStatus = Literal["started", "completed", "failed", "cancelled"]`
- `ModelInvocation`: id, request_id, provider, model, prompt_name, prompt_version, status, started_at, completed_at, latency_ms, input_tokens, output_tokens, total_tokens, estimated_cost_usd, finish_reason, retry_count, fallback_used, error_code, error_message.
- `InvocationRepository.create_started(request_id: str, provider: str, model: str, prompt_name: str | None, prompt_version: int | None) -> str`
- `InvocationRepository.complete(invocation_id: str, result: LLMResult, latency_ms: int, retry_count: int, fallback_used: bool) -> None`
- `InvocationRepository.fail(invocation_id: str, error: LLMError, latency_ms: int, retry_count: int, fallback_used: bool) -> None`
- `InvocationRepository.cancel(invocation_id: str, latency_ms: int) -> None`
- `InvocationRepository.get(invocation_id: str) -> ModelInvocation | None`

- [ ] **Step 1: Write integration tests for start, complete, failure, cancellation, redacted error fields, and lookup.**
- [ ] **Step 2: Run `make test-db-up && uv run pytest tests/test_invocations_integration.py -v`.** Expected: FAIL because the model, migration, and repository do not exist.
- [ ] **Step 3: Define the SQLAlchemy model with no raw prompt content, credentials, or provider response payload.** Store sanitized error code/message only.
- [ ] **Step 4: Add migration `0002_model_invocations` and import the model before Alembic reads metadata.**
- [ ] **Step 5: Implement repository operations using the existing async session factory and UTC timestamps.**
- [ ] **Step 6: Run `uv run alembic upgrade head`, the integration tests, and `uv run alembic downgrade base`.** Expected: all PASS.
- [ ] **Step 7: Run `make test-db-down`.** Expected: test database container and volume are removed.

### Task 6: Implement the generation service and retry/fallback policy

**Files:**
- Create: `src/contextwise/application/llm/generation_service.py`
- Create: `tests/test_generation_service.py`

**Interfaces:**
- `GenerationInput(prompt: str, model: str | None, prompt_name: str | None, prompt_version: int | None, response_schema: str | None, temperature: float | None, max_tokens: int | None)`
- `GenerationOutput(invocation_id: str, text: str, structured: BaseModel | None, provider: str, model: str, prompt_name: str | None, prompt_version: int | None, usage: LLMUsage, latency_ms: int, retry_count: int, fallback_used: bool, finish_reason: str | None)`
- `GenerationService.generate(input: GenerationInput, request_id: str) -> GenerationOutput`
- `GenerationService.stream(input: GenerationInput, request_id: str) -> AsyncIterator[LLMStreamChunk]`

- [ ] **Step 1: Write failing service tests for success, timeout retry, rate-limit retry, non-retryable failure, fallback disclosure, bounded structured repair, and persistence status transitions.**
- [ ] **Step 2: Run `uv run pytest tests/test_generation_service.py -v`.** Expected: FAIL because the service does not exist.
- [ ] **Step 3: Implement model and prompt resolution, then create a `started` invocation before the first upstream call.**
- [ ] **Step 4: Implement bounded retry with `LLM_MAX_RETRIES`; sleep only between retries using a small deterministic backoff based on attempt number.**
- [ ] **Step 5: After primary retries are exhausted, call the configured fallback once and set `fallback_used=True`; never fallback for invalid request or structured-output validation errors.**
- [ ] **Step 6: Validate named structured output with `TypeAdapter(model).validate_json(result.text)`; perform at most `LLM_STRUCTURED_REPAIR_ATTEMPTS` additional request(s), then fail with `structured_output_invalid`.**
- [ ] **Step 7: Update the invocation with usage, latency, finish reason, retry count, fallback flag, and sanitized failure data.**
- [ ] **Step 8: Run `uv run pytest tests/test_generation_service.py -v`.** Expected: PASS.

### Task 7: Add generation and inspection HTTP endpoints

**Files:**
- Modify: `src/contextwise/api/dependencies.py`
- Modify: `src/contextwise/api/main.py`
- Create: `src/contextwise/api/generations.py`
- Create: `src/contextwise/api/invocations.py`
- Create: `tests/test_generations.py`

**Interfaces:**
- `POST /v1/generations` accepts `GenerationRequest` and returns `GenerationResponse`.
- `POST /v1/generations/stream` accepts the same request and returns `text/event-stream`.
- `GET /v1/invocations/{invocation_id}` returns a redacted `InvocationResponse` or `404`.
- `GenerationResponse` includes invocation ID, text or structured object, provider, model, prompt version, usage, latency, retry count, fallback disclosure, and finish reason.
- The request ID comes from `request.state.request_id` and is passed into the service.

- [ ] **Step 1: Write API tests for free-form success, registered structured schema success, unknown model/prompt/schema validation, fallback metadata, HTTP error mapping, and invocation lookup.**
- [ ] **Step 2: Run `uv run pytest tests/test_generations.py -v`.** Expected: FAIL because the routes do not exist.
- [ ] **Step 3: Extend `AppState` with the registries, fake/LiteLLM clients, repository, and `GenerationService`; keep construction in dependencies rather than route functions.**
- [ ] **Step 4: Implement request/response Pydantic models and route handlers that only translate HTTP input/output.**
- [ ] **Step 5: Register the routers under `/v1` in `create_app()`.**
- [ ] **Step 6: Run `uv run pytest tests/test_generations.py -v`.** Expected: PASS.
- [ ] **Step 7: Run a local fake-provider request with `curl` and verify the response contains an invocation ID and `provider: "fake"`.**

### Task 8: Add registry endpoints and SSE streaming

**Files:**
- Modify: `src/contextwise/api/generations.py`
- Create: `src/contextwise/api/llm_registry.py`
- Modify: `src/contextwise/application/llm/generation_service.py`
- Modify: `tests/test_generations.py`
- Modify: `tests/test_llm_registry.py`

**Interfaces:**
- `GET /v1/models` returns configured model names, providers, and capabilities without secrets.
- `GET /v1/prompts` returns prompt names and versions without hidden credentials.
- SSE event format: `data: {"type":"chunk","text":"hello"}\n\n`, followed by `data: {"type":"completed","invocation_id":"abc123"}\n\n`.
- On upstream failure, emit one `error` event with an internal error code and close the stream.

- [ ] **Step 1: Write tests for model/prompt registry responses, ordered SSE chunks, completed event, partial-stream failure, and client cancellation.**
- [ ] **Step 2: Run `uv run pytest tests/test_generations.py tests/test_llm_registry.py -v`.** Expected: FAIL for the new cases.
- [ ] **Step 3: Implement `StreamingResponse` with an async generator that forwards internal chunks and finalizes invocation state.**
- [ ] **Step 4: Catch `asyncio.CancelledError`, mark the invocation cancelled, close the upstream iterator where supported, and re-raise cancellation.**
- [ ] **Step 5: Ensure no response headers or SSE payload contain provider API keys or raw provider errors.**
- [ ] **Step 6: Run the focused tests.** Expected: PASS.

### Task 9: Add secret-redaction and adapter-boundary regression coverage

**Files:**
- Create: `tests/test_llm_logging.py`
- Modify: `src/contextwise/infrastructure/llm/litellm_client.py`
- Modify: `src/contextwise/logging_config.py` only if a redaction fix is demonstrated by the tests.

- [ ] **Step 1: Write tests that submit a fake provider error containing a credential-shaped value and assert logs/API errors/persisted invocation errors do not contain it.**
- [ ] **Step 2: Run `uv run pytest tests/test_llm_logging.py -v`.** Expected: FAIL if any boundary leaks the value.
- [ ] **Step 3: Add the smallest boundary-level redaction needed; do not add a general-purpose logging framework.**
- [ ] **Step 4: Run the test and inspect captured JSON logs.** Expected: PASS and no credential-shaped value present.

### Task 10: Create the frozen evaluation and milestone evidence

**Files:**
- Create: `experiments/provider-baseline-001/prompts.jsonl`
- Create: `experiments/provider-baseline-001/run.py`
- Create: `experiments/provider-baseline-001/README.md`
- Create: `docs/learning/01-llm-gateway.md`
- Create: `docs/RELEASE_NOTES/0.1.0.md`
- Modify: `docs/milestones/01-llm-gateway-typed-generation.md`

- [ ] **Step 1: Freeze exactly 30 prompts covering free-form answers, structured answers, short outputs, long outputs, and malformed/failure cases.** Store stable IDs and expected evaluation dimensions; do not include secrets.
- [ ] **Step 2: Implement `run.py` to execute the dataset through application services, record provider/model/prompt version, time to first token, total latency, validity, token usage, estimated cost, retries, fallback, and status.**
- [ ] **Step 3: Run the fake configuration and label it as a deterministic plumbing baseline.**
- [ ] **Step 4: Run a configured LiteLLM provider only when credentials are explicitly present; otherwise record that the real-provider comparison is unavailable rather than fabricating results.**
- [ ] **Step 5: Compare free-form JSON prompting with registered schema-constrained generation and write the observed results to the experiment README.**
- [ ] **Step 6: Write the learning note, release notes, API examples, limitations, and deferred work.**
- [ ] **Step 7: Update Milestone 1 checkboxes only from committed artifacts and observed command output.**

### Task 11: Run the complete verification gate

**Files:**
- No source changes unless a verification failure is caused by this milestone.

- [ ] **Step 1: Run `uv run ruff check src tests`.** Expected: PASS.
- [ ] **Step 2: Run `uv run ruff format --check src tests`.** Expected: PASS.
- [ ] **Step 3: Run `uv run mypy src`.** Expected: PASS.
- [ ] **Step 4: Run `make test`.** Expected: all deterministic tests PASS.
- [ ] **Step 5: Run `make test-integration`.** Expected: invocation persistence and migrations PASS.
- [ ] **Step 6: Run the fake-provider demo for free-form, structured, and streamed requests.** Expected: all three responses are documented and invocations are inspectable.
- [ ] **Step 7: Review the Milestone 1 acceptance criteria line by line.** Leave any criterion unchecked if remote-provider, evaluation, or security evidence is unavailable.

## Completion Criteria

Milestone 1 is ready for its exit review only when the fake adapter, LiteLLM boundary, free-form and structured endpoints, SSE cancellation path, registries, invocation persistence, retry/fallback policy, secret-redaction tests, and frozen evaluation artifacts all have passing evidence. A missing real-provider key may block only the real-provider comparison, not deterministic plumbing tests; it must be recorded explicitly rather than hidden.
