# Milestone 3 — Document Ingestion Pipeline

**Release target:** `v0.3`  
**Tier:** A  
**Effort band:** Medium  
**Depends on:** Milestone 2 exit gate

## 1. Goal

Build a safe, idempotent document pipeline before semantic question answering.

## 2. Primary User Story

> As a user, I can upload Markdown, text, and PDF files, observe processing status, retry failures, and retain exact provenance from stored file to extracted passage.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- untrusted file handling
- object-storage abstraction
- background jobs
- idempotent pipelines
- document parsing and normalization
- hashing, deduplication, and versioning
- provenance and source-location preservation

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] upload endpoint
- [ ] local object-store adapter
- [ ] file hashing and deduplication
- [ ] MIME, extension, and size validation
- [ ] Markdown, TXT, and PDF parsers
- [ ] normalization pipeline
- [ ] document and version entities
- [ ] background ingestion job
- [ ] processing status and error reporting
- [ ] reprocessing endpoint

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define document identity versus document version identity.
- [ ] Specify the ingestion state machine.
- [ ] Define parser output with page, section, and character-offset metadata.
- [ ] Define retry and idempotency keys.
- [ ] Document file-size, MIME, timeout, and storage limits.

### 6.2 Implementation

- [ ] Implement `ObjectStore` and local adapter.
- [ ] Persist the original bytes before parsing.
- [ ] Compute content hashes.
- [ ] Implement upload validation and rejection reasons.
- [ ] Implement Markdown and text parsers.
- [ ] Implement PDF parsing with page provenance.
- [ ] Normalize whitespace without destroying source locations.
- [ ] Create jobs with status, attempts, cancellation, and trace IDs.
- [ ] Persist extracted text separately from original files.
- [ ] Implement retry and reprocess flows.

### 6.3 Deterministic and Integration Tests

- [ ] Corrupt PDF.
- [ ] Encrypted PDF.
- [ ] Empty document.
- [ ] Duplicate upload.
- [ ] Same filename with different bytes.
- [ ] Parser timeout.
- [ ] Worker restart during processing.
- [ ] Repeated job delivery.
- [ ] Oversized upload.
- [ ] Unsupported MIME type.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Create a parser fixture set with expected passages and source locations.
- [ ] Measure extraction completeness and location accuracy for at least 15 representative documents.

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

- [ ] Repeated ingestion does not create duplicate records or segments.
- [ ] Original bytes and extracted text are separately retained.
- [ ] Every extracted segment maps to a document version and source location.
- [ ] Failed jobs are observable, retryable, and safe to repeat.
- [ ] Unsupported and unsafe files fail before expensive processing.

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

- [ ] `docs/learning/03-ingestion.md`
- [ ] parser fixture dataset
- [ ] ingestion state diagram
- [ ] failure matrix
- [ ] tag `contextwise-v0.3-ingestion`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Upload one file of each supported type.
2. Show processing states.
3. Open a stored passage and trace it to its source page.
4. Upload a duplicate.
5. Force and retry a parser failure.


## 11. Reflection Questions

- Which normalization steps damage provenance?
- Where should deduplication occur?
- What must be transactional in an ingestion pipeline?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 4, verify:

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
