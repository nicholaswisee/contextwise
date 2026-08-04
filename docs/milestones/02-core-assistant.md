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

- [ ] conversation and message APIs
- [ ] streaming chat
- [ ] conversation list and retrieval
- [ ] response regeneration
- [ ] conversation branching
- [ ] model switching
- [ ] system prompt registry
- [ ] context builder with token budgeting
- [ ] conversation title generation
- [ ] multimodal-ready message schema

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define conversation, message, branch, and generation ownership.
- [ ] Specify the ordering and precedence of system, developer, user, memory, and evidence context.
- [ ] Define token-budget allocation rules.
- [ ] Specify idempotency behavior for streamed requests.
- [ ] Decide what debug context is safe to expose.

### 6.2 Implementation

- [ ] Implement `ConversationService`.
- [ ] Implement message persistence and ordering.
- [ ] Implement `ContextBuilder` with deterministic token budgeting.
- [ ] Store prompt version and selected message IDs on every invocation.
- [ ] Add regenerate behavior without mutating the original answer.
- [ ] Add branch creation from an earlier message.
- [ ] Add model selection and simple task-based defaults.
- [ ] Generate titles asynchronously or with a lower-cost model.
- [ ] Define image/file message parts without yet implementing full ingestion.

### 6.3 Deterministic and Integration Tests

- [ ] Test message ordering and branch ancestry.
- [ ] Test context truncation at boundary conditions.
- [ ] Test duplicate client retries with idempotency keys.
- [ ] Test partial stream failure without duplicate assistant messages.
- [ ] Test prompt-version persistence.
- [ ] Test unauthorized conversation access.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Create 20 multi-turn cases with pronouns, corrections, and conflicting instructions.
- [ ] Compare full transcript, sliding window, and summary memory.
- [ ] Measure quality, tokens, latency, and context-overflow rate.

### 6.5 Documentation and Cleanup

- [ ] Update the architecture diagram if boundaries changed.
- [ ] Add or revise Architecture Decision Records for consequential choices.
- [ ] Update API or CLI documentation.
- [ ] Add a migration or upgrade note when persistent data changed.
- [ ] Record known limitations and deferred work.
- [ ] Complete the milestone retrospective template.
- [ ] Prepare a clean-checkout demo script.
- [ ] Tag the release only after the exit gate passes.

## 7. Acceptance Criteria

- [ ] The exact message set sent to the model can be reconstructed.
- [ ] Context overflow is deterministic and documented.
- [ ] Regeneration preserves the original answer.
- [ ] Branching creates an independent continuation.
- [ ] A failed or retried stream does not duplicate final messages.
- [ ] Prompt and model versions are stored for each assistant response.

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

- [ ] `docs/learning/02-context-management.md`
- [ ] context-strategy experiment report
- [ ] conversation domain diagram
- [ ] demo conversation export
- [ ] tag `contextwise-v0.2-assistant`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

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
- [ ] The demo works from a clean environment.
- [ ] Security and privacy review is complete.
- [ ] The learning note and retrospective are committed.
- [ ] The release tag exists and points to the evaluated commit.

**Decision:** `PASS / PASS WITH DOCUMENTED DEBT / FAIL`

A “pass with documented debt” is acceptable only for non-critical scope. It is not acceptable for data isolation, authorization, citation integrity, destructive actions, secrets, or unrecoverable migrations.
