# Milestone 5 — Hybrid Retrieval and Reranking

**Release target:** `v0.5`  
**Tier:** A  
**Effort band:** Large  
**Depends on:** Milestone 4 exit gate

## 1. Goal

Improve retrieval recall and precision using sparse search, fusion, filtering, reranking, and diversity controls.

## 2. Primary User Story

> As a user, I receive better evidence for exact terms, semantic questions, and filtered collections without losing provenance or making retrieval uninspectable.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- PostgreSQL full-text search
- dense and sparse retrieval differences
- reciprocal-rank fusion
- metadata filtering
- cross-encoder or LLM reranking
- deduplication and diversity
- offline ranking metrics and trade-offs

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] PostgreSQL full-text index
- [ ] sparse retriever
- [ ] dense+sparse fusion
- [ ] metadata and collection filters
- [ ] date and document-type filters
- [ ] reranker interface and one adapter
- [ ] deduplication and diversity selection
- [ ] retrieval configuration registry
- [ ] comparison dashboard or report

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define one retrieval pipeline contract with pluggable stages.
- [ ] Specify rank-fusion strategy and parameters.
- [ ] Define filter application order.
- [ ] Define reranker candidate limits and budgets.
- [ ] Define how near-duplicate chunks are detected.

### 6.2 Implementation

- [ ] Implement normalized sparse queries.
- [ ] Implement dense and sparse candidate retrieval.
- [ ] Implement reciprocal-rank fusion.
- [ ] Add metadata and date filtering.
- [ ] Add reranker adapter.
- [ ] Add result deduplication by content hash or similarity.
- [ ] Add diversity selection across documents/sections.
- [ ] Persist stage scores and ranks.
- [ ] Expose a stage-by-stage debug view.

### 6.3 Deterministic and Integration Tests

- [ ] Test exact identifier and rare-term retrieval.
- [ ] Test semantic paraphrase retrieval.
- [ ] Test filter isolation and invalid filters.
- [ ] Test stable fusion with tied ranks.
- [ ] Test reranker timeout and fallback.
- [ ] Test deduplication without removing distinct evidence.
- [ ] Test retrieval configuration versioning.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Freeze the Milestone 4 dataset before changes.
- [ ] Measure dense baseline, sparse baseline, fusion, fusion+rerank, and fusion+rerank+diversity.
- [ ] Report Recall@k, Precision@k, MRR, nDCG, citation coverage, latency, and cost.
- [ ] Perform query-category analysis rather than only aggregate scoring.

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

- [ ] Hybrid retrieval beats the frozen dense baseline on agreed priority metrics.
- [ ] The improvement is described with practical effect sizes and failure categories.
- [ ] Every run stores index and retrieval configuration versions.
- [ ] Reranker failure degrades gracefully.
- [ ] Debug output explains contribution from each retrieval stage.

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

- [ ] `docs/learning/05-hybrid-retrieval.md`
- [ ] hybrid retrieval benchmark
- [ ] retrieval-stage architecture diagram
- [ ] ADR for reranker choice
- [ ] tag `contextwise-v0.5-hybrid`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Run an exact-term query, a paraphrase query, and a filtered query.
2. Show dense and sparse candidates.
3. Show fused and reranked order.
4. Compare results against the v0.4 baseline.


## 11. Reflection Questions

- Which query classes benefit from sparse search?
- When does reranking cost more than it improves?
- How should diversity be balanced against pure relevance?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 6, verify:

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
