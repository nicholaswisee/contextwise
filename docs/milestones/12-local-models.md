# Milestone 12 — Local Models and Inference Engineering

**Release target:** `v0.12`  
**Tier:** C  
**Effort band:** Medium  
**Depends on:** Milestone 11 exit gate

## 1. Goal

Understand the quality, privacy, latency, throughput, and hardware trade-offs of local inference.

## 2. Primary User Story

> As a user, I can run selected Contextwise workflows in a privacy mode that prevents external model calls and clearly communicates local-model capability limits.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- model serving and health checks
- quantization
- VRAM/RAM and context pressure
- time to first token and throughput
- local/cloud routing
- privacy-aware inference
- benchmarking hardware-dependent systems

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] Ollama adapter
- [ ] local model registry
- [ ] hardware and memory reporting
- [ ] warmup and readiness checks
- [ ] privacy mode
- [ ] cloud/local routing policy
- [ ] benchmark harness
- [ ] local-model capability matrix

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define model capability metadata.
- [ ] Define privacy mode guarantees.
- [ ] Choose benchmark hardware-report format.
- [ ] Define warmup, unload, and health behavior.
- [ ] Define when local routing is allowed or prohibited.

### 6.2 Implementation

- [ ] Implement local adapter behind `LLMClient`.
- [ ] Discover or configure local models.
- [ ] Report context window, quantization, and hardware requirements.
- [ ] Implement warmup and readiness.
- [ ] Prevent cloud fallback in privacy mode.
- [ ] Add task-class routing rules.
- [ ] Measure memory during runs.
- [ ] Add benchmark export.

### 6.3 Deterministic and Integration Tests

- [ ] Local server unavailable.
- [ ] Model missing.
- [ ] Out-of-memory condition.
- [ ] Context too large.
- [ ] Privacy mode attempts cloud fallback.
- [ ] Structured output incompatibility.
- [ ] Concurrent request pressure.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Benchmark structured extraction, summarization, RAG Q&A, tool selection, code explanation, and long-context synthesis.
- [ ] Record quality, tokens/second, time to first token, RAM/VRAM, failure rate, context capacity, and machine-time proxy.

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

- [ ] Selected workflows run without cloud access.
- [ ] Privacy mode has no silent external fallback.
- [ ] Routing decisions are traceable.
- [ ] Local models are compared with cloud baselines rather than assumed equivalent.
- [ ] Hardware and quantization are recorded with every benchmark.

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

- [ ] `docs/learning/12-local-inference.md`
- [ ] local model benchmark report
- [ ] capability matrix
- [ ] routing ADR
- [ ] tag `contextwise-v0.12-local`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Enable privacy mode.
2. Run a supported task locally.
3. Show blocked cloud fallback.
4. Compare the same task with a cloud model.
5. Inspect resource usage.


## 11. Reflection Questions

- When is local inference operationally cheaper?
- Which task classes degrade most?
- How does quantization change quality and capacity?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 13, verify:

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
