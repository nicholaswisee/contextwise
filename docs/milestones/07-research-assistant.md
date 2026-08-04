# Milestone 7 — Research Assistant Workflow

**Release target:** `v0.7`  
**Tier:** B  
**Effort band:** Large  
**Depends on:** Milestone 6 exit gate

## 1. Goal

Build a deterministic and inspectable research pipeline before experimenting with multiple agents.

## 2. Primary User Story

> As a user, I can submit a research question and receive a saved Markdown report whose claims, sources, evidence, and system inferences are clearly distinguishable.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- workflow orchestration
- query planning
- web search and source retrieval
- source deduplication and provenance
- claim-evidence extraction
- long-context synthesis
- citation verification

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] research-run state machine
- [ ] research plan generation
- [ ] query generation
- [ ] web search adapter
- [ ] source retrieval and normalization
- [ ] duplicate detection
- [ ] source-quality metadata
- [ ] claim/evidence extraction
- [ ] citation-backed synthesis
- [ ] citation checker
- [ ] Markdown export and persistence

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define deterministic workflow states and retry boundaries.
- [ ] Define source, claim, evidence, and citation entities.
- [ ] Specify source-quality signals without pretending to fully automate credibility.
- [ ] Define paywall, robots, timeout, and unavailable-source handling.
- [ ] Define which output statements are source-derived versus system inference.

### 6.2 Implementation

- [ ] Implement plan generation as structured output.
- [ ] Generate bounded search queries.
- [ ] Retrieve and normalize source metadata.
- [ ] Store fetched snapshots or extracts subject to policy.
- [ ] Deduplicate URL variants and near-duplicate content.
- [ ] Extract claims and evidence into structured records.
- [ ] Synthesize a report section by section.
- [ ] Validate citations against stored evidence.
- [ ] Flag unsupported paragraphs.
- [ ] Persist runs and export Markdown.
- [ ] Support resume after partial failure.

### 6.3 Deterministic and Integration Tests

- [ ] Search-provider failure.
- [ ] Unavailable or paywalled source.
- [ ] Duplicate syndication.
- [ ] Contradictory sources.
- [ ] Unsupported generated citation.
- [ ] Research budget exceeded.
- [ ] Resume after worker interruption.
- [ ] Source content containing prompt injection.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Create 20 research tasks with a human rubric.
- [ ] Evaluate source coverage, claim support, citation validity, duplication, completeness, cost, and time.
- [ ] Compare one-shot report generation with the deterministic pipeline.

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

- [ ] Every factual claim is traceable to evidence or explicitly marked as inference.
- [ ] Unsupported paragraphs are caught by the checker.
- [ ] Failed sources do not collapse the entire workflow.
- [ ] Duplicate sources do not inflate evidence.
- [ ] Runs can be resumed without repeating completed expensive steps.

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

- [ ] `docs/learning/07-research-workflow.md`
- [ ] 20-case research dataset
- [ ] sample cited reports
- [ ] workflow state diagram
- [ ] tag `contextwise-v0.7-research`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Run a small research task.
2. Inspect the plan and queries.
3. Open collected sources and extracted claims.
4. Show an unsupported paragraph being flagged.
5. Export the report.


## 11. Reflection Questions

- Where did deterministic stages outperform a free-form agent?
- How should contradictory evidence be represented?
- What does a citation checker actually prove?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 8, verify:

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
