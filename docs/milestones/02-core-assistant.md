# Milestone 2 — Contextwise Core Assistant

**Release target:** `v0.2`  
**Tier:** A  
**Effort band:** Medium  
**Depends on:** Milestone 1 exit gate

## 1. Goal

Build a usable conversational assistant with explicit and inspectable context management.

## 2. Primary User Story

> As a user, I can maintain conversations, stream replies, switch models, regenerate or branch a response, and inspect which messages and prompt version were sent to the model.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- prompt hierarchy and prompt versioning
- conversation persistence
- context windows and token budgeting
- truncation and summarization strategies
- idempotency for streamed writes
- task-to-model matching
- multimodal message abstraction

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [x] conversation and message APIs
- [x] streaming chat
- [x] conversation list and retrieval
- [x] response regeneration
- [x] conversation branching
- [x] model switching
- [x] system prompt registry
- [x] context builder with token budgeting
- [x] conversation title generation
- [x] multimodal-ready message schema

## 6. Task Checklist

### 6.1 Design Before Coding

- [x] Define conversation, message, branch, and generation ownership.
- [x] Specify the ordering and precedence of system, developer, user, memory, and evidence context.
- [x] Define token-budget allocation rules.
- [x] Specify idempotency behavior for streamed requests.
- [x] Decide what debug context is safe to expose.

### 6.2 Implementation

- [x] Implement `ConversationService`.
- [x] Implement message persistence and ordering.
- [x] Implement `ContextBuilder` with deterministic token budgeting.
- [x] Store prompt version and selected message IDs on every invocation.
- [x] Add regenerate behavior without mutating the original answer.
- [x] Add branch creation from an earlier message.
- [x] Add model selection and simple task-based defaults.
- [x] Generate titles asynchronously or with a lower-cost model.
- [x] Define image/file message parts without yet implementing full ingestion.

### 6.3 Deterministic and Integration Tests

- [x] Test message ordering and branch ancestry.
- [x] Test context truncation at boundary conditions.
- [x] Test duplicate client retries with idempotency keys.
- [x] Test partial stream failure without duplicate assistant messages.
- [x] Test prompt-version persistence.
- [x] Test unauthorized conversation access.

### 6.4 Behavioral Evaluation and Measurement

- [x] Create 20 multi-turn cases with pronouns, corrections, and conflicting instructions.
- [x] Compare full transcript, sliding window, and summary memory.
- [x] Measure quality, tokens, latency, and context-overflow rate.

### 6.5 Documentation and Cleanup

- [x] Update the architecture diagram if boundaries changed.
- [x] Add or revise Architecture Decision Records for consequential choices.
- [x] Update API or CLI documentation.
- [x] Add a migration or upgrade note when persistent data changed.
- [x] Record known limitations and deferred work.
- [x] Complete the milestone retrospective template.
- [x] Prepare a clean-checkout demo script.
- [ ] Tag the release only after the exit gate passes.

## 7. Acceptance Criteria

- [x] The exact message set sent to the model can be reconstructed.
- [x] Context overflow is deterministic and documented.
- [x] Regeneration preserves the original answer.
- [x] Branching creates an independent continuation.
- [x] A failed or retried stream does not duplicate final messages.
- [x] Prompt and model versions are stored for each assistant response.

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

- [x] `docs/learning/02-context-management.md`
- [x] context-strategy experiment report
- [x] conversation domain diagram
- [x] demo conversation export
- [ ] tag `contextwise-v0.2-assistant`

Also attach or link:

- [x] one successful trace;
- [x] one representative failure trace;
- [x] benchmark or evaluation output;
- [x] release notes describing user-visible and architectural changes;
- [x] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Create a conversation.
2. Show multi-turn reference resolution.
3. Inspect the assembled context.
4. Regenerate one response.
5. Branch from an earlier turn and compare outcomes.


## 11. Reflection Questions

- When should old messages be summarized rather than dropped?
- What context should never be included automatically?
- What does conversation branching reveal about data modeling?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 3, verify:

- [ ] All required deliverables are complete or explicitly removed through an ADR.
- [ ] All acceptance criteria pass.
- [ ] Required tests pass locally and in CI.
- [ ] The behavioral evaluation has a stored baseline.
- [x] The demo works from a clean environment.
- [x] Security and privacy review is complete.
- [ ] The learning note and retrospective are committed.
- [ ] The release tag exists and points to the evaluated commit.

**Decision:** `PASS / PASS WITH DOCUMENTED DEBT / FAIL`

**Current result:** `IMPLEMENTED LOCALLY — EXIT GATE OPEN`. Local behavior,
evaluation, and security review are complete; a committed release revision,
remote CI evidence, and the required tag are still missing. ADR-0002 records
the limited exception for unresolved Milestone 1 evidence debt.

A “pass with documented debt” is acceptable only for non-critical scope. It is not acceptable for data isolation, authorization, citation integrity, destructive actions, secrets, or unrecoverable migrations.
