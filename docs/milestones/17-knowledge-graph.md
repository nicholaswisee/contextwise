# Milestone 17 — Knowledge Graph Experiment

**Release target:** `v0.17`  
**Tier:** D  
**Effort band:** Large  
**Depends on:** Milestone 16 exit gate

## 1. Goal

Determine through evidence whether graph structure improves specific retrieval tasks enough to justify its complexity.

## 2. Primary User Story

> As a user, I can explore entities and relationships linked to source evidence and use graph-assisted retrieval only where it demonstrably helps.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- entity and relation extraction
- entity resolution
- graph provenance
- confidence and uncertainty
- multi-hop retrieval
- graph rebuilding and maintenance
- evaluating complexity versus benefit

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] entity and relation schemas
- [ ] extraction pipeline
- [ ] entity-resolution logic
- [ ] source-linked graph assertions
- [ ] graph store
- [ ] graph exploration endpoint or UI
- [ ] graph-assisted retrieval experiment
- [ ] rebuild pipeline

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Choose a narrow graph use case and entity ontology.
- [ ] Define assertion, evidence, confidence, extractor, and version fields.
- [ ] Define entity-resolution strategy.
- [ ] Define graph storage choice and exit strategy.
- [ ] Define comparison tasks against hybrid retrieval.

### 6.2 Implementation

- [ ] Extract candidate entities and relations from stored documents.
- [ ] Persist evidence links for every node and edge assertion.
- [ ] Implement deterministic normalization and assisted resolution.
- [ ] Support human inspection of low-confidence merges.
- [ ] Build graph traversal queries.
- [ ] Add graph-assisted candidate retrieval.
- [ ] Combine graph and hybrid evidence without losing provenance.
- [ ] Implement complete rebuild from source documents.

### 6.3 Deterministic and Integration Tests

- [ ] Same-name unrelated entities.
- [ ] Aliases and abbreviations.
- [ ] Contradictory relations.
- [ ] Deleted or reprocessed source document.
- [ ] Low-confidence assertion.
- [ ] Graph rebuild.
- [ ] Cross-workspace graph isolation.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Test multi-hop questions, entity-centric browsing, and relationship discovery.
- [ ] Compare graph-assisted retrieval with Milestone 5 hybrid retrieval on quality, cost, latency, and maintenance effort.
- [ ] Measure incorrect merges and unsupported edge rate.

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

- [ ] Every node and edge maps to source evidence.
- [ ] LLM-extracted relations are not treated as unqualified facts.
- [ ] Graph-assisted retrieval is benchmarked against the existing baseline.
- [ ] The graph can be rebuilt from authoritative sources.
- [ ] The project records whether the graph is retained, narrowed, or removed.

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

- [ ] `docs/learning/17-knowledge-graph.md`
- [ ] graph benchmark report
- [ ] ontology and provenance specification
- [ ] retain/reject ADR
- [ ] tag `contextwise-v0.17-graph`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Index a graph-enabled collection.
2. Inspect an entity and its evidence-backed edges.
3. Answer a multi-hop question.
4. Compare hybrid-only and graph-assisted retrieval.
5. Rebuild the graph.


## 11. Reflection Questions

- Which graph assertions are observations and which are interpretations?
- Did graph structure improve retrieval or only visualization?
- What is the operational cost of entity resolution?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 18, verify:

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
