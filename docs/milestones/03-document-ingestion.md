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

- [x] upload endpoint
- [x] local object-store adapter
- [x] file hashing and deduplication
- [x] MIME, extension, and size validation
- [x] Markdown, TXT, and PDF parsers
- [x] normalization pipeline
- [x] document and version entities
- [x] background ingestion job
- [x] processing status and error reporting
- [x] reprocessing endpoint

## 6. Task Checklist

### 6.1 Design Before Coding

- [x] Define document identity versus document version identity.
- [x] Specify the ingestion state machine.
- [x] Define parser output with page, section, and character-offset metadata.
- [x] Define retry and idempotency keys.
- [x] Document file-size, MIME, timeout, and storage limits.

### 6.2 Implementation

- [x] Implement `ObjectStore` and local adapter.
- [x] Persist the original bytes before parsing.
- [x] Compute content hashes.
- [x] Implement upload validation and rejection reasons.
- [x] Implement Markdown and text parsers.
- [x] Implement PDF parsing with page provenance.
- [x] Normalize whitespace without destroying source locations.
- [x] Create jobs with status, attempts, cancellation, and trace IDs.
- [x] Persist extracted text separately from original files.
- [x] Implement retry and reprocess flows.

### 6.3 Deterministic and Integration Tests

- [x] Corrupt PDF.
- [x] Encrypted PDF.
- [x] Empty document.
- [x] Duplicate upload.
- [x] Same filename with different bytes.
- [x] Parser timeout.
- [x] Worker restart during processing.
- [x] Repeated job delivery.
- [x] Oversized upload.
- [x] Unsupported MIME type.

### 6.4 Behavioral Evaluation and Measurement

- [x] Create a parser fixture set with expected passages and source locations.
- [x] Measure extraction completeness and location accuracy for at least 15 representative documents.

### 6.5 Documentation and Cleanup

- [x] Update the architecture diagram if boundaries changed.
- [x] Add or revise Architecture Decision Records for consequential choices.
- [x] Update API or CLI documentation.
- [x] Add a migration or upgrade note when persistent data changed.
- [x] Record known limitations and deferred work.
- [x] Complete the milestone retrospective template.
- [x] Prepare a clean-checkout demo script.
- [ ] Tag the release only after the exit gate passes.

## 7. Acceptance Criteria

- [x] Repeated ingestion does not create duplicate records or segments.
- [x] Original bytes and extracted text are separately retained.
- [x] Every extracted segment maps to a document version and source location.
- [x] Failed jobs are observable, retryable, and safe to repeat.
- [x] Unsupported and unsafe files fail before expensive processing.

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

- [x] `docs/learning/03-ingestion.md`
- [x] parser fixture dataset
- [x] ingestion state diagram
- [x] failure matrix
- [ ] tag `contextwise-v0.3-ingestion`

Also attach or link:

- [x] one successful trace;
- [x] one representative failure trace;
- [x] benchmark or evaluation output;
- [x] release notes describing user-visible and architectural changes;
- [x] open issues for consciously deferred work.

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

- [x] All required deliverables are complete or explicitly removed through an ADR.
- [x] All acceptance criteria pass.
- [x] Required tests pass locally and in CI.
- [x] The behavioral evaluation has a stored baseline.
- [x] The demo works from a clean environment.
- [x] Security and privacy review is complete for the local single-owner scope.
- [x] The learning note and retrospective are committed.
- [ ] The release tag exists and points to the evaluated commit.

**Decision:** `IMPLEMENTED — EXIT GATE OPEN`

The ingestion code at `c1542df` passed 78 local unit tests, 23 local
PostgreSQL integration tests, the Docker smoke demo, and [remote check,
migration, and integration jobs](https://github.com/nicholaswisee/contextwise/actions/runs/37859902740).
The 15-document parser fixture set passed extraction and location checks.
The release tag and final exit decision remain open.

A “pass with documented debt” is acceptable only for non-critical scope. It is not acceptable for data isolation, authorization, citation integrity, destructive actions, secrets, or unrecoverable migrations.
