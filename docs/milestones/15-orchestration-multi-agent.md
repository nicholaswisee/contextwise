# Milestone 15 — Controlled Orchestration and Multi-Agent Experiments

**Release target:** `v0.15`  
**Tier:** D  
**Effort band:** Large  
**Depends on:** Milestone 14 exit gate

## 1. Goal

Learn orchestration only after deterministic workflows and single-agent tool loops are reliable.

## 2. Primary User Story

> As a user, I can run a complex task through an explicit, resumable workflow and see whether specialized agents actually improve results over simpler baselines.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- workflow versus agent distinctions
- typed state machines
- delegation and coordination overhead
- parallel work and merge strategies
- review loops
- termination and convergence
- human approval checkpoints

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] typed workflow state
- [ ] planner/researcher/writer/reviewer/finalizer experiment
- [ ] step budgets
- [ ] retry and resume
- [ ] parallel research branches
- [ ] review feedback loop
- [ ] termination rules
- [ ] approval checkpoints
- [ ] baseline comparison

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define the task set where orchestration might help.
- [ ] Define explicit workflow states and transitions.
- [ ] Define per-step inputs, outputs, and budgets.
- [ ] Define loop termination and maximum revision count.
- [ ] Define what human approval can pause or alter.

### 6.2 Implementation

- [ ] Implement handwritten orchestration first.
- [ ] Persist workflow state and checkpoints.
- [ ] Add idempotent steps and resume.
- [ ] Parallelize independent retrieval tasks.
- [ ] Implement reviewer feedback as structured output.
- [ ] Prevent reviewer-added unsupported claims.
- [ ] Add deterministic termination.
- [ ] Trace every inter-agent message.
- [ ] Optionally evaluate a workflow framework only after an ADR.

### 6.3 Deterministic and Integration Tests

- [ ] Step timeout.
- [ ] Worker interruption and resume.
- [ ] Repeated delivery.
- [ ] Reviewer/writer loop.
- [ ] Agent returns malformed state.
- [ ] Parallel branch failure.
- [ ] Unsupported reviewer suggestion.
- [ ] Budget exhaustion.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Compare single prompt, deterministic multi-step workflow, one agent with tools, and multiple specialized agents on a frozen complex-task set.
- [ ] Measure task success, quality, latency, cost, calls, and coordination failures.

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

- [ ] Multi-agent complexity is retained only if it beats simpler baselines on meaningful tasks.
- [ ] Every state transition and inter-agent message is traceable.
- [ ] The workflow cannot loop indefinitely.
- [ ] Failed work can resume without repeating completed steps.
- [ ] Human checkpoints are explicit and auditable.

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

- [ ] `docs/learning/15-orchestration.md`
- [ ] orchestration benchmark
- [ ] workflow state diagram
- [ ] framework adoption or rejection ADR
- [ ] tag `contextwise-v0.15-orchestration`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Run one complex task through each baseline.
2. Show workflow state and parallel branches.
3. Interrupt and resume.
4. Show reviewer feedback and termination.
5. Compare cost and quality.


## 11. Reflection Questions

- Did specialization improve results or merely add calls?
- Which stages should remain deterministic?
- What failure patterns emerge only from coordination?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 16, verify:

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
