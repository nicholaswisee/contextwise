# Milestone 14 — Coding Assistant and Repository Intelligence

**Release target:** `v0.14`  
**Tier:** C  
**Effort band:** Large  
**Depends on:** Milestone 13 exit gate

## 1. Goal

Apply retrieval, provenance, tools, and incremental indexing to source-code repositories.

## 2. Primary User Story

> As a developer, I can index a repository, ask architectural and code questions, receive file-and-line citations, and update the index efficiently after a new commit.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- code-aware parsing and chunking
- symbol and dependency metadata
- lexical, semantic, and structural retrieval
- incremental indexing
- commit provenance
- static-analysis integration
- limitations of inferred architecture

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] Git repository ingestion
- [ ] language-aware parsers where practical
- [ ] symbol/file/dependency metadata
- [ ] commit-aware incremental indexing
- [ ] repository Q&A
- [ ] file and line citations
- [ ] architecture summaries
- [ ] documentation generation
- [ ] read-only review suggestions

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define repository, commit, file version, symbol, and dependency entities.
- [ ] Define code chunking by symbol and syntax boundaries.
- [ ] Define incremental invalidation rules.
- [ ] Define citation format for files and line ranges.
- [ ] Define observed facts versus inferred architecture.

### 6.2 Implementation

- [ ] Clone or read configured repositories safely.
- [ ] Record commit and file hashes.
- [ ] Parse supported languages with tree-sitter or language tools.
- [ ] Extract symbols, imports, paths, and metadata.
- [ ] Index code lexically and semantically.
- [ ] Build symbol and dependency search.
- [ ] Combine retrieval stages.
- [ ] Generate cited repository answers.
- [ ] Generate architecture summaries with explicit inference labels.
- [ ] Update only changed/deleted files on new commits.
- [ ] Integrate read-only linters or static analyzers.

### 6.3 Deterministic and Integration Tests

- [ ] Binary and generated files.
- [ ] Large files.
- [ ] Renamed, deleted, and moved files.
- [ ] Changed symbols with same name.
- [ ] Unsupported language.
- [ ] Submodules or ignored directories.
- [ ] Citation line drift after re-index.
- [ ] Repository access isolation.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Create repository questions for symbols, call paths, configuration, architecture, and likely bugs.
- [ ] Measure retrieval recall, citation validity, answer correctness, index update time, and unsupported-claim rate.

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

- [ ] Answers cite exact files and line ranges.
- [ ] Only changed content is re-indexed.
- [ ] Generated explanations distinguish code facts from architectural inference.
- [ ] Review suggestions do not claim runtime defects without evidence.
- [ ] The repository index is tied to a commit.

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

- [ ] `docs/learning/14-code-intelligence.md`
- [ ] repository benchmark dataset
- [ ] incremental indexing report
- [ ] sample architecture summary
- [ ] tag `contextwise-v0.14-code`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Index a repository.
2. Ask where a feature is implemented.
3. Trace a symbol or dependency.
4. Commit a small change.
5. Show incremental indexing and updated citations.


## 11. Reflection Questions

- Why is code retrieval structurally different from prose retrieval?
- Which architecture claims can be directly observed?
- When should static analysis override model speculation?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 15, verify:

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
