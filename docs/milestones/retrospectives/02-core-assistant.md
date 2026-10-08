# Contextwise Milestone Retrospective

**Milestone:** 2 — Contextwise Core Assistant
**Date:** 2026-10-09
**Release tag:** Not created; exit gate remains open.

## 1. What Was Built

The service now persists owned conversations and immutable message parts,
selects deterministic text context, records invocation provenance before
streaming, supports safe retries, regenerates sibling answers, copies branch
ancestry, and exposes REST/SSE routes plus authenticated context inspection.

## 2. What Was Learned

The difficult part of streaming chat is not forwarding chunks; it is making the
accepted request, placeholder, invocation, context snapshot, and terminal state
agree across retries and disconnects. Branching also confirmed that copied
ancestry needs new IDs plus source IDs, rather than mutating a shared tree.

## 3. Evidence and Result

- Focused assistant, generation, API, repository, and migration tests pass
  locally. The Docker smoke demo passes two turns, context inspection,
  regeneration, and branching through the public API.
- The frozen context evaluation contains 20 cases × 3 strategies = 60 rows.
- The checked-in result artifact contains no raw prompt, response, or
  credential fields.
- The fake provider proves deterministic plumbing only; no real-provider quality
  comparison is claimed.

## 4. Important Failures

- The first shared stream refactor failed to close its inner generator when the
  consumer closed early; the outer stream now closes it explicitly so invocation
  cancellation is persisted.
- Strict mypy required explicit SQLAlchemy result typing at repository query
  boundaries.

## 5. Architecture Decisions

- A local owner token is the smallest safe authorization boundary for this
  single-user API.
- `ModelInvocation` remains the authoritative provider lifecycle record.
- Context is snapshotted before provider iteration and inspected from durable
  data, not reconstructed.
- M2 drops old context deterministically and defers automated summaries.

## 6. Security and Privacy Review

The completed local review covers owner-token checks on every model and
conversation route, owner-scoped repository lookups, sanitized invocation
errors, unsupported-part rejection, context inspection, and the production
token setting. It is scoped to the single-owner local service.

## 7. Deferred Work

- Replace the local token with a real identity boundary.
- Add measured tokenizer validation and memory/summarization policy.
- Add retrieval, ingestion, and provider-native multimodal support in their
  later milestones.
- Run real-provider evaluation and complete remote CI and provider security
  evidence inherited from Milestone 1.

Tracked as CW-01 through CW-04 in `docs/issues/README.md`.

## 8. Exit Decision

`IMPLEMENTED LOCALLY — EXIT GATE OPEN`

The implementation, local deterministic evidence, security review, and live
demo are present. The release evidence has not been committed, remote CI is
unverified, and the required tag does not exist. ADR-0002 explicitly permits
the non-critical Milestone 1 evidence debt while leaving that gate open.
