# Contextwise Milestone Retrospective

**Milestone:** 1 — LLM Gateway and Typed Generation
**Release tag:** Not required for this project.
**Date completed:** 2026-09-04
**Commit evaluated:** Milestone 1 branch after local quality and integration verification.

## 1. What Was Built

The gateway accepts generation requests, resolves a registered model and prompt version, persists an invocation lifecycle record, returns free-form or validated structured output, and streams deterministic fake-provider chunks through SSE. It uses a Contextwise-owned `LLMClient` interface with fake and LiteLLM adapters.

## 2. What Was Learned

- Provider SDK types remain replaceable when only infrastructure imports them.
- A fake adapter makes timeouts, fallback, schema validation, and stream cancellation testable without credentials.
- Invocation persistence must begin before the first provider call and must not store raw prompts or provider payloads.

## 3. Baseline and Result

- Dataset/version: `experiments/provider-baseline-001/prompts.jsonl` with 30 fixed cases.
- Candidate configuration: fake provider with `fake-default`.
- Quality result: all 10 registered-schema cases validated; fake output is a plumbing result, not a model-quality claim.
- Latency result: stored in `results.jsonl` per case.
- Cost result: zero for fake provider calls.
- Failure-rate result: deterministic tests cover timeout retry, fallback disclosure, invalid structured output, partial stream failure, and consumer cancellation.

## 4. Important Failures

- Strict mypy rejected the initial untyped SQLAlchemy base; switching to `DeclarativeBase` fixed the mapped-model type boundary.
- Persistence tests were initially unmarked and therefore skipped by `make test-integration`; they now carry the integration marker.
- The first stream implementation emitted an already-completed response; it was replaced with upstream chunk forwarding and cancellation handling.

## 5. Architecture Decisions

- Fake provider is the default local model.
- LiteLLM is the only provider dependency and is isolated under `infrastructure/llm`.
- Fallback is permitted only before a stream begins and is returned in invocation/API metadata.
- Structured output uses named registered Pydantic models.

## 6. Security and Privacy Review

Provider error content is reduced to internal error codes in HTTP responses and persisted failures. Full security review remains outstanding because the team-mode audit is unavailable.

## 7. Operational Review

- Invocation records expose status, latency, tokens, zero fake-provider cost, retry count, fallback use, and finish reason.
- The deterministic fake baseline contains no provider credentials or raw prompt persistence.
- Real-provider latency, cost, and time-to-first-token measurements require explicit credentials.

## 8. Demonstration

See [`docs/demos/01-llm-gateway-demo.md`](../../demos/01-llm-gateway-demo.md) and [`experiments/provider-baseline-001/`](../../../experiments/provider-baseline-001/).

## 9. Deferred Work

- Run the same frozen prompts against two explicitly configured providers.
- Add provider-specific cost reconciliation.
- Add a full security review and remote CI evidence.

## 10. Exit Decision

`PASS WITH DOCUMENTED DEBT`

The deterministic gateway is implemented and locally verified. The exit gate remains open for real-provider comparison, remote CI evidence, and the full security review.
