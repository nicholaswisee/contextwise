# Milestone 9 — Observability and Operational Analytics

**Release target:** `v0.9`  
**Tier:** B  
**Effort band:** Medium  
**Depends on:** Milestone 8 exit gate

## 1. Goal

Make Contextwise explainable to its operator through correlated traces, metrics, logs, and cost records.

## 2. Primary User Story

> As the operator, I can trace a request across API, retrieval, model calls, tools, jobs, and persistence, and answer where time, money, and failures are concentrated.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- traces, metrics, and logs
- OpenTelemetry context propagation
- AI-specific spans and attributes
- Langfuse traces and prompt metadata
- cost attribution
- SLO-oriented dashboards
- error taxonomy and failure analysis

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] OpenTelemetry instrumentation
- [ ] Langfuse integration
- [ ] structured logs with trace correlation
- [ ] application and AI metrics
- [ ] cost dashboard
- [ ] latency dashboard
- [ ] error taxonomy
- [ ] prompt/model comparison views
- [ ] user feedback capture

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define trace naming and required attributes.
- [ ] Define metrics with units, labels, and cardinality constraints.
- [ ] Define secret and PII redaction.
- [ ] Define the error taxonomy and ownership.
- [ ] Choose initial service-level indicators.

### 6.2 Implementation

- [ ] Instrument HTTP requests and application services.
- [ ] Instrument prompt assembly and model calls.
- [ ] Instrument embedding, retrieval, reranking, tools, database calls, and jobs.
- [ ] Propagate trace IDs across the queue.
- [ ] Record p50/p95/p99 latency and time to first token.
- [ ] Track tokens and cost by feature/model/workspace.
- [ ] Track retrieval empty rate and tool failure rate.
- [ ] Add feedback endpoints.
- [ ] Build dashboards or saved queries.

### 6.3 Deterministic and Integration Tests

- [ ] Trace continuity across background jobs.
- [ ] Redaction of secrets and sensitive fields.
- [ ] Failure spans contain typed error categories.
- [ ] Metric labels do not contain unbounded user input.
- [ ] Sampling does not remove required audit events.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Use a scripted workload to generate representative traffic.
- [ ] Identify the slowest stage, highest-cost feature, most common failure, and one misleading metric.
- [ ] Document one optimization hypothesis without implementing it yet.

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

- [ ] A single trace explains a complete request path.
- [ ] Dashboards answer which prompt regressed, which model is cheapest by task, which tool fails most, and which retrieval stage is slowest.
- [ ] Usage and cost totals reconcile with invocation records.
- [ ] Sensitive values are not present in logs or traces.

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

- [ ] `docs/learning/09-observability.md`
- [ ] dashboard screenshots or exports
- [ ] error taxonomy
- [ ] sample end-to-end trace
- [ ] tag `contextwise-v0.9-observability`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Run a RAG or research request.
2. Open its trace.
3. Show model, retrieval, database, and tool spans.
4. Show cost and latency dashboards.
5. Filter by one error category.


## 11. Reflection Questions

- Which metric was initially easy to misinterpret?
- What belongs in an audit log rather than an observability trace?
- How does instrumentation alter architecture?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 10, verify:

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
