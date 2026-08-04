# Milestone 19 — AI Engineering Playground

**Release target:** `v1.0`  
**Tier:** D  
**Effort band:** Large  
**Depends on:** Milestone 18 exit gate

## 1. Goal

Turn Contextwise into a durable experimentation platform where production defaults are linked to reproducible evidence.

## 2. Primary User Story

> As the project owner, I can define, run, compare, and reproduce experiments across prompts, models, embeddings, chunking, rerankers, and routing policies, then promote a winning configuration.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- experiment design
- configuration and dataset versioning
- parallel execution
- reproducibility limits in probabilistic systems
- statistical summaries
- promotion and rollback of AI configurations
- preserving failed experiments as evidence

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] experiment definition format
- [ ] dataset selector
- [ ] prompt/model matrix
- [ ] embedding/chunking/reranker matrix
- [ ] stored configuration and environment metadata
- [ ] parallel execution
- [ ] result comparison
- [ ] statistical summaries
- [ ] Markdown/HTML export
- [ ] promotion workflow

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define experiment identity, hypothesis, factors, controls, datasets, repetitions, metrics, and success criteria.
- [ ] Define reproducibility metadata.
- [ ] Define production configuration references.
- [ ] Define promotion approval and rollback.
- [ ] Define retention policy for experiment artifacts.

### 6.2 Implementation

- [ ] Create experiment schema and CLI/API.
- [ ] Select versioned datasets and evaluators.
- [ ] Generate configuration matrices.
- [ ] Execute trials with bounded parallelism.
- [ ] Store traces and result artifacts.
- [ ] Support repeated runs and aggregate variance.
- [ ] Generate comparison tables and plots or reports.
- [ ] Link production defaults to experiment IDs.
- [ ] Implement promotion and rollback of configuration bundles.
- [ ] Retain failed and inconclusive experiments.

### 6.3 Deterministic and Integration Tests

- [ ] Invalid experiment configuration.
- [ ] Missing dataset or prompt version.
- [ ] Interrupted experiment resume.
- [ ] Provider outage during matrix run.
- [ ] Non-comparable metrics.
- [ ] Promotion of failed experiment.
- [ ] Rollback to previous configuration.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Reproduce at least three earlier milestone experiments through the playground: provider comparison, retrieval comparison, and routing comparison.
- [ ] Verify that conclusions match or explain differences.

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

- [ ] Every experiment is reproducible from stored configuration to the limits documented.
- [ ] Results include quality, latency, cost, errors, and variance.
- [ ] Production defaults reference successful experiment records.
- [ ] Promotion and rollback are auditable.
- [ ] Failed experiments remain searchable learning evidence.

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

- [ ] `docs/learning/19-playground.md`
- [ ] three reproduced benchmark reports
- [ ] experiment schema documentation
- [ ] production configuration manifest
- [ ] tag `contextwise-v1.0`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Define a prompt/model matrix.
2. Run it on a frozen dataset.
3. Compare results.
4. Promote the winner.
5. Run a smoke evaluation.
6. Roll back to the previous configuration.


## 11. Reflection Questions

- What does reproducibility mean when providers change models?
- Which experiments need repeated runs?
- How does promotion turn research output into production change management?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone Completion, verify:

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
