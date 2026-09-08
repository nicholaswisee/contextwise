# Milestone 1 — LLM Gateway and Typed Generation

**Release target:** `v0.1`  
**Tier:** A  
**Effort band:** Medium  
**Depends on:** Milestone 0 exit gate

## 1. Goal

Learn reliable model-call mechanics without agents or retrieval.

## 2. Primary User Story

> As a developer, I can submit a prompt, choose a model, receive streamed or structured output, and inspect exactly which provider, prompt version, latency, tokens, retries, and cost were involved.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- model request anatomy and message roles
- sampling and provider differences
- streaming lifecycle and cancellation
- schema-constrained generation
- provider abstraction and adapters
- timeouts, retries, rate limits, and fallbacks
- usage and cost accounting

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [x] provider-neutral `LLMClient` interface
- [x] LiteLLM adapter and fake test adapter
- [x] `POST /v1/generations`
- [x] `POST /v1/generations/stream` using SSE
- [x] schema-constrained generation with Pydantic
- [x] model registry endpoint
- [x] prompt registry with versions
- [x] persisted `ModelInvocation` records
- [x] timeout, retry, and explicit fallback policy

## 6. Task Checklist

### 6.1 Design Before Coding

- [x] Define internal request and response contracts independent of LiteLLM.
- [x] Define the invocation lifecycle and persistence states.
- [x] Specify retryable versus non-retryable errors.
- [x] Specify when fallback is allowed and how it is disclosed.
- [x] Define how cost estimates are calculated and reconciled.

### 6.2 Implementation

- [x] Create model, provider, and capability configuration.
- [x] Implement the fake provider before the real provider adapter.
- [x] Implement free-form generation.
- [x] Implement Pydantic schema validation and bounded repair/retry.
- [x] Implement SSE streaming with disconnect detection.
- [x] Persist invocation start, completion, failure, usage, and finish reason.
- [x] Expose invocation inspection endpoint.
- [x] Add provider timeout and retry handling.
- [x] Add at least two configurable providers or one provider plus Ollama.

### 6.3 Deterministic and Integration Tests

- [x] Contract-test every adapter against the internal interface.
- [x] Test malformed structured output.
- [x] Test upstream timeout and rate limit.
- [x] Test client cancellation during streaming.
- [x] Test provider fallback disclosure.
- [x] Test partial-stream failure and invocation persistence.
- [x] Verify secret values are redacted from API and persisted errors.

### 6.4 Behavioral Evaluation and Measurement

- [x] Create a frozen 30-prompt dataset.
- [ ] Compare two model/provider configurations on quality, time to first token, total latency, valid structured-output rate, tokens, and cost. The credential-safe comparison runner is implemented; measured evidence remains pending.
- [ ] Compare free-form JSON prompting with schema-constrained output. The current frozen cases are not paired for this comparison.

### 6.5 Documentation and Cleanup

- [ ] Update the architecture diagram if boundaries changed.
- [ ] Add or revise Architecture Decision Records for consequential choices.
- [x] Update API or CLI documentation.
- [x] Add a migration or upgrade note when persistent data changed.
- [x] Record known limitations and deferred work.
- [x] Complete the milestone retrospective template.
- [x] Prepare a clean-checkout demo script.
- Release tagging is not required for this project.

## 7. Acceptance Criteria

- [ ] Application services do not import provider SDKs.
- [ ] Malformed model output never reaches domain code as a valid object.
- [ ] Streaming cancellation stops upstream work where supported.
- [ ] Every invocation has a traceable provider, model, prompt version, usage, latency, and status.
- [ ] Fallbacks are visible in traces and API metadata.
- [ ] The 30-case baseline report is committed.

## 8. How to Know the Milestone Is Complete

Consider this milestone complete only when all of the following statements are true:

1. **It works:** the user story succeeds through a documented public interface.
2. **It is repeatable:** a clean checkout can reproduce the result.
3. **It is tested:** deterministic behavior and external boundaries have automated coverage.
4. **It is measured:** a frozen evaluation or benchmark exists for probabilistic behavior.
5. **It is observable:** a failure can be located using logs, traces, metrics, and persisted records.
6. **It is bounded:** security, privacy, cost, timeout, and failure implications are documented.
7. **It is explainable:** you can describe why the architecture exists and which alternatives were rejected.
8. **It improves the system:** the result is compared with a prior baseline or establishes the first baseline.
9. **It leaves evidence:** the required artifacts below are committed.
10. **The exit gate passes:** there are no unchecked acceptance criteria classified as required.

A feature that merely works in one manual demonstration does **not** complete the milestone.

## 9. Required Evidence

- [x] `docs/learning/01-llm-gateway.md`
- [x] `experiments/provider-baseline-001/`
- [x] prompt registry entries
- [x] invocation trace examples
- Release tag: not required for this project.

Also attach or link:

- [x] one successful trace;
- [x] one representative failure trace;
- [x] benchmark or evaluation output;
- [x] release notes describing user-visible and architectural changes;
- [x] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Generate an unstructured answer.
2. Generate a validated structured object.
3. Force a malformed test response and show the typed error.
4. Stream a response and cancel it.
5. Compare two invocation records.


## 11. Reflection Questions

- What behavior differed most across providers?
- Which failures should be retried?
- What information must be persisted before streaming begins?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 2, verify:

- [ ] All required deliverables are complete or explicitly removed through an ADR.
- [ ] All acceptance criteria pass.
- [ ] Required tests pass locally and in CI.
- [ ] The behavioral evaluation has a stored baseline.
- [ ] The demo works from a clean environment.
- [ ] Security and privacy review is complete.
- [ ] The learning note and retrospective are committed.

**Decision:** `IMPLEMENTED LOCALLY — EXIT GATE OPEN` — deterministic provider contracts, persistence, streaming, the 30-case fake baseline, and credential-safe comparison plumbing are complete. Credentialed real-provider measurement, paired quality/TTFT/cost evaluation, remote CI evidence, the full security review, and committing real-provider evidence remain outstanding; release tagging is not required.

A “pass with documented debt” is acceptable only for non-critical scope. It is not acceptable for data isolation, authorization, citation integrity, destructive actions, secrets, or unrecoverable migrations.
