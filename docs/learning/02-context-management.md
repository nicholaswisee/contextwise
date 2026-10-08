# Milestone 2 Learning Note — Context Management

**Date:** 2026-09-10

## What the implementation taught me

### Prompt precedence

The assistant resolves an immutable `system@1` definition from
`PromptRegistry`, then appends retained conversation messages in parent-to-child
order. M2 has no developer instructions, memory, or evidence segments, so the
builder does not invent them. `direct@1` remains available for the existing
generation endpoint.

### Token budgeting and truncation

The combined input and reserve budget is 4096 estimated tokens, with a 512-token
output reserve. The estimator is `ceil(characters / 4)`. The builder starts with
the complete eligible ancestry and removes the oldest message until the input
estimate plus reserve fits. It persists the selected IDs and `truncated` flag,
so inspection does not recompute an approximate context later.

Failed, cancelled, and streaming assistant placeholders never become ordinary
future context. Image and file references are stored as message parts but are
rejected by the current text-only request builder.

### Summaries

M2 does not automatically summarize. The frozen evaluation uses manually
authored summaries only to compare a summary strategy without introducing a
memory extractor ahead of the memory milestone. A production summary should be
added only with an explicit policy for provenance, freshness, and replacement.

### Streaming idempotency

The unique conversation/key claim and assistant placeholder commit before the
provider stream begins. Chunks update that same row. A completed or terminal
request replays its stored result, an active duplicate returns `409`, and a key
with a different fingerprint returns `422`. This makes client retries safe
without pretending provider streaming itself is transactional.

### Multimodal deferral

The message schema already accepts text, image-reference, and file-reference
parts. Only text parts can be rendered into the existing `LLMRequest`; no file
ingestion, image loading, retrieval, or provider-native multimodal call was
added. This preserves the data model without expanding the milestone boundary.

## Reflection questions

### When should old messages be summarized rather than dropped?

When dropping a message would repeatedly break a tested reference or
instruction, and the summary can be generated with provenance and a measurable
quality benefit. Until that evidence exists, deterministic dropping is easier
to inspect and safer than silently generated memory.

### What context should never be included automatically?

Provider credentials, raw provider errors, unrelated conversations, untrusted
retrieved text without a later retrieval policy, and failed or cancelled
assistant attempts should never enter the request by accident.

### What does branching reveal about data modeling?

Branching is not a mutable conversation fork. It is a new conversation whose
copied messages retain source IDs, while new messages use new IDs and parents.
That model makes future edits independent and keeps provenance inspectable.

## Evidence

- `tests/test_context_builder.py` covers ordering, truncation, unsupported parts,
  and terminal-message exclusion.
- `experiments/context-strategy-001/results.jsonl` contains 20 cases across
  three strategies and metadata only.
- `docs/adr/0002-core-assistant-boundaries.md` records the fixed policy values.
