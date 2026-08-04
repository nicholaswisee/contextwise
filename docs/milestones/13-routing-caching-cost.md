# Milestone 13 — Model Routing, Caching, and Cost Control

**Release target:** `v0.13`  
**Tier:** C  
**Effort band:** Large  
**Depends on:** Milestone 12 exit gate

## 1. Goal

Optimize the quality-cost-latency-privacy frontier without hiding degraded behavior.

## 2. Primary User Story

> As a user and operator, I receive an appropriate model for the task, benefit from safe caching, stay within configured budgets, and can see when fallback or degradation occurs.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- task classification
- policy-based model routing
- fallback and graceful degradation
- exact and semantic caching
- cache isolation and invalidation
- cost attribution and anomaly detection
- batch versus interactive inference

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] task classifier
- [ ] policy router
- [ ] fallback chains
- [ ] exact response cache
- [ ] optional semantic cache experiment
- [ ] prompt-prefix reuse where supported
- [ ] request/workspace budgets
- [ ] cost anomaly detection
- [ ] batch execution path
- [ ] routing analytics

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define routing inputs: task, capabilities, privacy, latency, context, quality, budget, provider health.
- [ ] Define routing priority and conflict resolution.
- [ ] Define cache keys and authorization scope.
- [ ] Define when cached AI outputs may be reused.
- [ ] Define fallback disclosure.

### 6.2 Implementation

- [ ] Implement deterministic task classification baseline.
- [ ] Implement policy evaluation and selected route persistence.
- [ ] Add provider-health inputs.
- [ ] Add explicit fallback chains.
- [ ] Implement exact cache with prompt/model/config/version keys.
- [ ] Partition caches by authorization scope.
- [ ] Experiment with semantic caching only on low-risk tasks.
- [ ] Enforce request and workspace budgets.
- [ ] Add cost anomaly alerts.
- [ ] Add batch execution for suitable offline work.

### 6.3 Deterministic and Integration Tests

- [ ] Cache cross-workspace isolation.
- [ ] Prompt or schema version invalidates cache.
- [ ] Fallback when provider is unhealthy.
- [ ] Privacy policy overrides cost policy.
- [ ] Budget exceeded.
- [ ] Semantic cache near-miss returns unsafe stale answer.
- [ ] Batch partial failure.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Compare router against a single-model baseline on the frozen evaluation suite.
- [ ] Measure quality, latency, cost, fallback rate, and cache correctness.
- [ ] Report the Pareto frontier, not only average savings.

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

- [ ] Router improves an agreed combination of cost, latency, or privacy without crossing quality floors.
- [ ] Cache hits preserve authorization and configuration correctness.
- [ ] Fallbacks are visible to traces and user-facing metadata where relevant.
- [ ] Budgets are enforceable.
- [ ] Production routes map to benchmark evidence.

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

- [ ] `docs/learning/13-routing-and-cost.md`
- [ ] router benchmark report
- [ ] cache safety test report
- [ ] routing policy configuration
- [ ] tag `contextwise-v0.13-routing`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Run several task classes.
2. Show different route decisions.
3. Trigger a provider fallback.
4. Demonstrate a valid cache hit and an invalidated cache.
5. Trigger a budget limit.


## 11. Reflection Questions

- What is the cost of a wrong routing decision?
- Which outputs are unsafe to cache semantically?
- How should quality floors differ by task?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 14, verify:

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
