# Milestone 10 — Evaluation System and Regression Gates

**Release target:** `v0.10`  
**Tier:** B  
**Effort band:** Large  
**Depends on:** Milestone 9 exit gate

## 1. Goal

Treat probabilistic behavior as testable product behavior and make quality regressions visible before release.

## 2. Primary User Story

> As the project owner, I can compare a candidate prompt, model, or retrieval configuration with a frozen baseline and block releases that fail critical quality or safety thresholds.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- golden datasets and representative sampling
- component versus end-to-end evaluation
- human rubrics
- LLM-as-judge limitations
- variance and flaky cases
- baseline comparison and release thresholds
- online versus offline evaluation

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] versioned datasets
- [ ] evaluation case schema
- [ ] evaluation runner
- [ ] metric registry
- [ ] human review files or UI
- [ ] baseline comparison
- [ ] CI smoke suite
- [ ] scheduled full evaluation
- [ ] release quality report
- [ ] regression gate configuration

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define dataset and case versioning.
- [ ] Separate deterministic, retrieval, generation, workflow, adversarial, and online evaluation layers.
- [ ] Define human review rubric.
- [ ] Define critical versus informational thresholds.
- [ ] Define repeated-run and variance policy.

### 6.2 Implementation

- [ ] Create dataset loaders.
- [ ] Create evaluators for schema validity, retrieval ranking, citation validity, tool selection, and safety rules.
- [ ] Integrate optional judge-model evaluators.
- [ ] Store all evaluation configuration and results.
- [ ] Build baseline-versus-candidate reports.
- [ ] Run a small deterministic subset in pull requests.
- [ ] Run the full suite manually or on schedule.
- [ ] Add release gates for critical regressions.
- [ ] Track flaky cases explicitly.

### 6.3 Deterministic and Integration Tests

- [ ] Evaluator correctness using known pass/fail fixtures.
- [ ] Dataset schema validation.
- [ ] Judge-provider failure.
- [ ] Partial evaluation resume.
- [ ] Baseline mismatch.
- [ ] Repeated-run variance.
- [ ] Critical safety threshold enforcement.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Reach at least 150 cases: 40 assistant/structured, 50 retrieval, 25 tool, 20 research, 15 adversarial.
- [ ] Calibrate judge-model scores against human review on a sample.
- [ ] Measure agreement and document weak categories.

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

- [ ] Every case records input, expected behavior, required evidence/tool calls, prohibited behavior, rubric, category, and difficulty.
- [ ] Prompt/model changes cannot pass critical gates when they regress.
- [ ] Scores store model, prompt, dataset, and configuration versions.
- [ ] Judge scores are not treated as ground truth without calibration.
- [ ] Flaky cases are labeled and investigated.

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

- [ ] `docs/learning/10-evaluation.md`
- [ ] `datasets/` version 1
- [ ] evaluation methodology document
- [ ] sample release quality report
- [ ] tag `contextwise-v0.10-evaluation`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Run the baseline suite.
2. Change a prompt to create a regression.
3. Show the failed gate.
4. Inspect component-level results.
5. Restore the prompt and rerun.


## 11. Reflection Questions

- Which metrics correlate poorly with human judgment?
- What makes a dataset representative?
- When should a release be blocked despite an improved average score?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 11, verify:

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
