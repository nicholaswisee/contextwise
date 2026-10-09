# ADR-0002: Core Assistant Boundaries

**Status:** Accepted
**Date:** 2026-09-10
**Milestone:** 2 — Contextwise Core Assistant

## Context

Milestone 2 adds durable user-owned conversations to an API that currently has
no identity or authorization concept. It also needs to make context selection,
streaming lifecycle, retries, regeneration, and branching inspectable without
introducing a queue, tokenizer, retrieval system, or second provider layer.

Milestone 1 explicitly records:

> **Decision:** `IMPLEMENTED LOCALLY — EXIT GATE OPEN` — deterministic provider
> contracts, persistence, streaming, the 30-case fake baseline, and
> credential-safe comparison plumbing are complete. Credentialed real-provider
> measurement, paired quality/TTFT/cost evaluation, remote CI evidence, the full
> security review, and committing real-provider evidence remain outstanding;
> release tagging is not required.

The same milestone states that pass with documented debt is not acceptable for
data isolation, authorization, secrets, or unrecoverable migrations.

## Decision Drivers

- data isolation and explicit authorization;
- deterministic, reproducible context selection;
- retry-safe persistence before a provider stream;
- preserving the existing provider-neutral generation service;
- low operational and dependency complexity;
- a clear learning boundary for later memory and multimodal milestones.

## Considered Options

### Option A — Begin M2 with a documented non-critical M1 exception

Carry only the open M1 evidence debt that does not affect M2's authorization,
secrets, data isolation, or migration safety. Record this ADR before adding
user-data persistence.

### Option B — Block all M2 implementation until M1 is fully closed

This would wait for credentialed provider measurements, remote CI evidence, and
the full team security review even though those items are not prerequisites for
the local conversation slice.

### Option C — Add conversations without an explicit owner boundary

This would minimize initial code but would expose user data without a defined
authorization contract and would violate the M2 security requirement.

## Decision

### Milestone 1 prerequisite

Choose **Option A**. M2 implementation may begin because the unresolved M1
items are credentialed measurement, paired quality/TTFT/cost evaluation,
remote CI evidence, and the full security review. They remain documented debt;
they do not close the M1 gate and must not be represented as a passing M1
release. M2 must independently verify authorization, data isolation, secrets,
and reversible migrations before claiming its own exit gate.

### Ownership and authorization

Use one configured local owner token, `CONTEXTWISE_OWNER_TOKEN`, mapped to the
fixed owner ID `local`. Conversation routes require the exact
`X-Contextwise-Owner` header. Missing or invalid tokens return HTTP `401`.
Resource lookups always scope by `owner_id`; an unowned or missing resource is
reported as `404` after authentication succeeds. This is a single-user local
boundary, not general multi-user authentication.

### Context precedence and budgets

The conceptual order is system prompt, developer instructions, retained
conversation messages, memory, and evidence. M2 supplies only the resolved
versioned system prompt and retained conversation messages. It never fabricates
developer instructions, memory, or evidence.

The combined input-plus-reserve budget is **4096 tokens**. The output reserve
is **512 tokens**, leaving at most 3584 estimated input tokens. The local
deterministic estimator is `ceil(number_of_characters / 4)`, with an empty
string estimating zero. Context selection preserves parent-to-child order and
drops the oldest complete retained message first until the budget fits. Failed,
cancelled, and streaming assistant messages are excluded from ordinary future
context.

### Idempotent streamed generations

A unique `(conversation_id, idempotency_key)` identifies one accepted streamed
generation. The request fingerprint covers the conversation, message parts,
model, prompt version, temperature, and output limit. The unique claim and
streaming assistant placeholder are committed before any provider iteration.

Completed and terminal failed/cancelled requests replay their stored terminal
result without another provider call. An active duplicate returns `409`. A key
reused with a different fingerprint returns `422`; a new attempt uses a new
key. Client disconnects and provider failures update the same placeholder and
invocation rather than creating a duplicate final message.

### Branching and regeneration

Branching copies the selected source conversation's ancestor chain through the
requested message into a new conversation. Each copied message retains its
source conversation/message IDs for provenance. Future messages in the branch
are independent. Regeneration creates a sibling assistant message below the
same user parent and never mutates the original assistant message.

### Prompt and title behavior

`direct@1` remains the existing user-prompt definition. The assistant uses an
immutable `system@1` registry definition for the system segment and persists
the resolved prompt name/version with each assistant invocation. Titles are
unset unless an explicitly configured lower-cost registered title model exists.
Title generation runs only after the first successful assistant response, and
title failure cannot fail chat completion.

### Safe debug exposure

The context inspection endpoint exposes persisted prompt/version metadata,
model/provider metadata, request settings, rendered provider messages, ordered
selected message IDs, token estimates, and truncation state. It never exposes
provider credentials, raw provider error payloads, or secret-bearing settings.
Message content is exposed only through the authenticated owner's own context
inspection route.

## Consequences

### Positive

- User-data routes have an explicit and testable ownership boundary.
- The exact context used for a generation can be reconstructed from durable
  snapshots rather than recomputed guesses.
- Retries, regeneration, and branches have stable persistence semantics.
- The implementation remains provider-neutral and dependency-light.

### Negative

- The single local token is not suitable for multi-user deployment.
- Character estimation is intentionally approximate and may under- or
  over-estimate provider tokenization.
- M2 drops old context rather than implementing automated summaries.
- Title generation is optional and may leave conversations untitled.

### Risks

- Operators must set a non-default owner token outside source control before
  exposing the service beyond local development.
- The open M1 security and credentialed-measurement debt remains open.
- Context inspection is intentionally powerful for debugging and must remain
  owner-scoped.

## Exit Strategy

Replace the local token dependency with a real identity provider while keeping
the repository owner predicates unchanged. Replace the estimator with a
measured tokenizer only after an evaluation demonstrates material budget
defects. Add summaries, memory, evidence, and multimodal provider requests in
later milestones without changing the immutable message and invocation
provenance model.

## Validation

- contract and context-builder tests cover precedence, unsupported parts,
  ordering, and boundary truncation;
- PostgreSQL integration tests cover owner scoping, idempotency uniqueness,
  branch provenance, and migration round trips;
- service/API tests cover replay, partial failure, regeneration, branching,
  context inspection, and unauthorized access;
- the frozen 20-case context-strategy evaluation records quality and resource
  metrics without raw prompts, responses, or credentials.
