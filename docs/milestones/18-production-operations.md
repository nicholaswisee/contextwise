# Milestone 18 — Production Operations

**Release target:** `v0.18`  
**Tier:** D  
**Effort band:** Large  
**Depends on:** Milestone 17 exit gate

## 1. Goal

Operate Contextwise as a dependable service with tested recovery, deployment, and rollback procedures.

## 2. Primary User Story

> As the operator, I can deploy, monitor, back up, restore, migrate, scale, and roll back Contextwise using documented and rehearsed procedures.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- container image design
- reverse proxy and TLS
- durable jobs and worker scaling
- backup and restore
- schema migration strategy
- deployment and rollback
- service-level objectives and runbooks
- optional Kubernetes justification

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [ ] production Docker images
- [ ] Docker Compose deployment
- [ ] reverse proxy and TLS
- [ ] database backup and restore
- [ ] object-storage lifecycle policy
- [ ] worker scaling
- [ ] migration procedure
- [ ] deployment pipeline
- [ ] rollback process
- [ ] alerts and runbooks
- [ ] optional Kubernetes experiment

## 6. Task Checklist

### 6.1 Design Before Coding

- [ ] Define deployment environments and configuration separation.
- [ ] Define RPO, RTO, availability, latency, ingestion delay, worker success, and quality floors.
- [ ] Define backup scope and retention.
- [ ] Define migration compatibility rules.
- [ ] Define rollback triggers and ownership.

### 6.2 Implementation

- [ ] Create minimal non-root production images.
- [ ] Add Compose profiles for API, worker, database, object store, telemetry, and proxy.
- [ ] Configure TLS.
- [ ] Automate database backups.
- [ ] Back up required object-store metadata or objects.
- [ ] Implement durable worker queues if not already done.
- [ ] Add deployment automation.
- [ ] Implement expand/migrate/contract or other safe schema process.
- [ ] Create rollback commands.
- [ ] Create operational alerts linked to runbooks.
- [ ] Evaluate Kubernetes only if a documented need exists.

### 6.3 Deterministic and Integration Tests

- [ ] Restore database and object data into a clean environment.
- [ ] Rollback application after a failed deployment.
- [ ] Restart API during long-running jobs.
- [ ] Restart worker during job execution.
- [ ] Run migration with old and new application versions where required.
- [ ] Expire TLS or simulate proxy failure.
- [ ] Simulate provider and database outage.

### 6.4 Behavioral Evaluation and Measurement

- [ ] Run a game-day exercise covering deployment failure, database restore, worker interruption, and provider outage.
- [ ] Record recovery time, data loss, alert quality, and missing runbook steps.

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

- [ ] A backup is restored successfully in a clean environment.
- [ ] Rollback is rehearsed.
- [ ] Liveness and readiness remain distinct.
- [ ] Long jobs survive API restarts and safely retry worker interruption.
- [ ] Alerts identify user impact and link to current runbooks.
- [ ] Optional Kubernetes adoption has a documented operational justification.

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

- [ ] `docs/learning/18-operations.md`
- [ ] `docs/runbooks/`
- [ ] backup/restore transcript
- [ ] game-day report
- [ ] tag `contextwise-v0.18-production`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [ ] release notes describing user-visible and architectural changes;
- [ ] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Deploy a release.
2. Start a long job and restart the API.
3. Restore a backup into a clean environment.
4. Deploy a deliberately broken version and roll back.
5. Show an alert and runbook.


## 11. Reflection Questions

- Which recovery assumptions were false?
- What complexity would Kubernetes add here?
- Which SLO best represents actual user value?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 19, verify:

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
