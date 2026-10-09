# Milestone 4 — Manual Dense Retrieval and Cited RAG

**Release target:** `v0.4`  
**Tier:** A  
**Effort band:** Large  
**Depends on:** Milestone 3 exit gate

## 1. Goal

Understand the essential RAG pipeline by implementing chunking, embeddings, retrieval, context assembly, and citations manually.

## 2. Primary User Story

> As a user, I can ask a question over selected documents, receive an evidence-grounded answer, open every citation, and inspect what was retrieved even when the answer is insufficient.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- chunking strategies and trade-offs
- embedding generation and indexing
- vector similarity
- retrieval versus generation failures
- evidence-object design
- context construction under token budgets
- mechanically traceable citations

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [x] configurable chunker
- [x] embedding service interface
- [x] cloud embedding adapter
- [x] pgvector schema and indexes
- [x] dense retriever; local baseline is lexical, cloud semantic run pending
- [x] top-k and score controls
- [x] evidence object model
- [x] RAG context builder
- [x] cited answer generator
- [x] retrieval debug endpoint
- [x] insufficient-evidence behavior

## 6. Task Checklist

### 6.1 Design Before Coding

- [x] Define chunk identity and index versioning.
- [x] Specify evidence fields and citation format.
- [x] Define retrieval-run persistence.
- [x] Define how selected collections constrain retrieval.
- [x] Specify abstention and uncertainty rules.

### 6.2 Implementation

- [x] Implement fixed-token chunking with overlap.
- [x] Implement heading-aware chunking.
- [x] Persist chunks with source metadata.
- [x] Implement batching, retries, and rate-limit handling for embeddings.
- [x] Store embedding model and index version.
- [x] Implement cosine-distance retrieval through pgvector.
- [x] Return evidence objects rather than prompt strings.
- [x] Build evidence context within a token budget.
- [x] Generate answers that cite evidence IDs.
- [x] Validate that citations reference retrieved evidence.
- [x] Add retrieval-only and full-RAG debug endpoints.

### 6.3 Deterministic and Integration Tests

- [x] Test chunk boundary and overlap behavior.
- [x] Test source-location preservation.
- [x] Test embedding retry and partial batch failure.
- [x] Test workspace and collection isolation.
- [x] Test empty retrieval.
- [x] Test invalid citation IDs.
- [x] Test context assembly exceeding token budget.
- [x] Test re-indexing without mixing versions.

### 6.4 Behavioral Evaluation and Measurement

- [x] Create at least 50 labeled retrieval questions.
- [x] For each case, record relevant document and acceptable answer passage.
- [x] Run chunk-size, overlap, top-k, heading-aware, query-rewrite, and embedding-model experiments.
- [x] Measure Recall@k, answer support, citation validity, latency, and cost.

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

- [x] Every citation resolves to a stored source passage.
- [x] Retrieval can be evaluated without generation.
- [x] The system qualifies or refuses unsupported answers.
- [x] At least 50 labeled cases are frozen.
- [x] Every retrieval run records query, configuration, index version, candidates, and selected evidence.
- [x] A baseline report identifies the dominant failure categories.

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

- [x] `docs/learning/04-manual-rag.md`
- [x] `datasets/retrieval/v1/`
- [x] chunking benchmark report
- [x] retrieval failure taxonomy
- [ ] tag `contextwise-v0.4-rag`

Also attach or link:

- [x] one successful trace;
- [x] one representative failure trace;
- [x] benchmark or evaluation output;
- [x] release notes describing user-visible and architectural changes;
- [x] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Index a small collection.
2. Ask a supported question and open citations.
3. Ask an unsupported question and show abstention.
4. Inspect the retrieval debug output.
5. Change top-k and compare results.


## 11. Reflection Questions

- Did failures originate in ingestion, chunking, retrieval, context, or generation?
- Which chunking strategy was best for which document type?
- Why is a similarity score not a probability of relevance?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 5, verify:

- [x] All required deliverables are complete or explicitly removed through an ADR.
- [x] All acceptance criteria pass.
- [ ] Required tests pass locally and in CI.
- [x] The behavioral evaluation has a stored baseline.
- [x] The demo works from a clean environment.
- [x] Security and privacy review is complete for the local single-owner scope.
- [ ] The learning note and retrospective are committed.
- [ ] The release tag exists and points to the evaluated commit.

**Decision:** `IMPLEMENTED — EXIT GATE OPEN`

The local 50-case hash-embedding baseline and live Docker demo pass. The
credentialed semantic-provider baseline is deferred as CW-09; the local hash
model measures lexical projection only. Required remote CI and the release
tag remain open. See `docs/evaluations/04-rag-report.md` and
`docs/security/04-rag-review.md` for measured behavior and limits.

A “pass with documented debt” is acceptable only for non-critical scope. It is not acceptable for data isolation, authorization, citation integrity, destructive actions, secrets, or unrecoverable migrations.
