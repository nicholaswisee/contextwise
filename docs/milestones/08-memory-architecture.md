# Milestone 8 — Memory Architecture

**Release target:** `v0.8`  
**Tier:** B  
**Effort band:** Large  
**Depends on:** Milestone 7 exit gate

## 1. Goal

Implement memory as explicit, inspectable data products rather than unlimited transcript accumulation.

## 2. Primary User Story

> As a user, I can approve, inspect, edit, expire, and delete retained memories, and Contextwise can explain why a memory was selected for a response.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- state versus memory
- working, conversational, semantic, episodic, and knowledge memory
- memory extraction and consolidation
- relevance, recency, and confidence scoring
- privacy, sensitivity, and retention
- contradiction and supersession
- context compression

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] memory item model
- [ ] memory extraction pipeline
- [ ] approval and editing controls
- [ ] sensitivity levels
- [ ] retrieval scoring
- [ ] expiration and deletion
- [ ] conflict detection
- [ ] supersession history
- [ ] context compression
- [ ] memory-use explanation

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define what is never automatically memorized.
- [ ] Define memory categories, sensitivity, source, confidence, and retention.
- [ ] Specify user approval requirements.
- [ ] Define conflict and supersession behavior.
- [ ] Define memory retrieval scoring and token budget.

### 6.2 Implementation

- [ ] Implement candidate memory extraction from completed conversations.
- [ ] Require policy and optional user approval before persistence.
- [ ] Build inspect, edit, delete, and export APIs.
- [ ] Implement expiration and cleanup jobs.
- [ ] Implement relevance, recency, confidence, and scope scoring.
- [ ] Add conflict detection and supersession links.
- [ ] Inject selected memory through `ContextBuilder`.
- [ ] Record exactly which memories influenced a response.
- [ ] Generate concise conversation summaries separately from semantic memory.

### 6.3 Deterministic and Integration Tests

- [ ] Sensitive content is excluded by default.
- [ ] Deleted memory cannot be retrieved.
- [ ] Expired memory is not used.
- [ ] Conflicting facts do not silently coexist as equally current.
- [ ] Memory from another workspace is inaccessible.
- [ ] Poisoned or injected content cannot grant permissions.
- [ ] Summary regeneration preserves provenance.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Create personalization tasks where approved memory should help and privacy tasks where it must not be used.
- [ ] Measure task success, irrelevant-memory rate, stale-memory rate, token savings, and privacy violations.

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

- [ ] Not every message becomes a memory.
- [ ] Users can inspect, correct, and delete retained memories.
- [ ] Sensitive memory follows explicit policy.
- [ ] Every used memory is logged with selection rationale.
- [ ] Memory improves a frozen benchmark without unacceptable privacy failures.

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

- [ ] `docs/learning/08-memory.md`
- [ ] memory policy
- [ ] memory benchmark report
- [ ] data-retention diagram
- [ ] tag `contextwise-v0.8-memory`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Create an approved preference memory.
2. Use it in a later conversation.
3. Show why it was selected.
4. Edit it and demonstrate changed behavior.
5. Delete it and verify it is no longer used.


## 11. Reflection Questions

- What is the difference between a conversation summary and a fact about the user?
- When should confidence decay?
- How can memory improve utility while reducing user control?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 9, verify:

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
