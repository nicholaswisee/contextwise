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

- [ ] configurable chunker
- [ ] embedding service interface
- [ ] cloud embedding adapter
- [ ] pgvector schema and indexes
- [ ] semantic retriever
- [ ] top-k and score controls
- [ ] evidence object model
- [ ] RAG context builder
- [ ] cited answer generator
- [ ] retrieval debug endpoint
- [ ] insufficient-evidence behavior

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define chunk identity and index versioning.
- [ ] Specify evidence fields and citation format.
- [ ] Define retrieval-run persistence.
- [ ] Define how selected collections constrain retrieval.
- [ ] Specify abstention and uncertainty rules.

### 6.2 Implementation

- [ ] Implement fixed-token chunking with overlap.
- [ ] Implement heading-aware chunking.
- [ ] Persist chunks with source metadata.
- [ ] Implement batching, retries, and rate-limit handling for embeddings.
- [ ] Store embedding model and index version.
- [ ] Implement cosine-distance retrieval through pgvector.
- [ ] Return evidence objects rather than prompt strings.
- [ ] Build evidence context within a token budget.
- [ ] Generate answers that cite evidence IDs.
- [ ] Validate that citations reference retrieved evidence.
- [ ] Add retrieval-only and full-RAG debug endpoints.

### 6.3 Deterministic and Integration Tests

- [ ] Test chunk boundary and overlap behavior.
- [ ] Test source-location preservation.
- [ ] Test embedding retry and partial batch failure.
- [ ] Test workspace and collection isolation.
- [ ] Test empty retrieval.
- [ ] Test invalid citation IDs.
- [ ] Test context assembly exceeding token budget.
- [ ] Test re-indexing without mixing versions.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Create at least 50 labeled retrieval questions.
- [ ] For each case, record relevant document/chunk or acceptable passage.
- [ ] Run chunk-size, overlap, top-k, heading-aware, query-rewrite, and embedding-model experiments.
- [ ] Measure Recall@k, answer support, citation validity, latency, and cost.

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

- [ ] Every citation resolves to a stored source passage.
- [ ] Retrieval can be evaluated without generation.
- [ ] The system qualifies or refuses unsupported answers.
- [ ] At least 50 labeled cases are frozen.
- [ ] Every retrieval run records query, configuration, index version, candidates, and selected evidence.
- [ ] A baseline report identifies the dominant failure categories.

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

- [ ] `docs/learning/04-manual-rag.md`
- [ ] `datasets/retrieval/v1/`
- [ ] chunking benchmark report
- [ ] retrieval failure taxonomy
- [ ] tag `contextwise-v0.4-rag`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

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
