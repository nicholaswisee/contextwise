# Milestone 0 — Engineering Foundation

**Release target:** `v0.0`  
**Tier:** A  
**Effort band:** Small  
**Depends on:** Project brief and repository bootstrap  
**Prerequisites:** [`docs/PREREQUISITES.md`](../PREREQUISITES.md) — verify the toolchain before starting

## 1. Goal

Create a disciplined, reproducible Python service before introducing model or agent complexity.

## 2. Primary User Story

> As the project owner, I can clone the repository, start the complete local stack with one command, inspect health status, and run the same checks locally that CI runs.

## 3. Why This Milestone Exists

This milestone is a learning unit, a product release, and an engineering proof point. Do not optimize for feature count. Optimize for a narrow vertical slice that can be demonstrated, tested, measured, and explained.

## 4. What You Should Learn

- Python package and application structure
- async lifecycle and graceful shutdown
- FastAPI dependency injection
- Pydantic settings and configuration validation
- SQLAlchemy sessions and Alembic migrations
- structured logging and request correlation
- unit, integration, and migration testing

At the end, you should be able to explain these topics without relying on framework slogans and show where each concept appears in the codebase.

## 5. Required Deliverables

- [x] Repository bootstrapping with a reproducible package manager
- [x] FastAPI application factory
- [x] `GET /health/live` and `GET /health/ready`
- [x] environment-based settings with startup validation
- [x] PostgreSQL connection and initial Alembic migration
- [x] structured JSON logs and request IDs
- [x] Docker Compose for API and database
- [x] CI for linting, formatting, typing, tests, and migrations

## 6. Task Checklist

### 6.1 Design Before Coding

- [x] Choose `uv` or Poetry and record the decision in an ADR.
- [x] Define the top-level package boundaries: API, application, domain, infrastructure.
- [x] Specify the standard API error envelope.
- [x] Decide how local, test, and production settings are loaded.
- [ ] Draw a one-page startup and shutdown lifecycle diagram.

### 6.2 Implementation

- [x] Create the application factory and router registration.
- [x] Implement typed settings with required and optional variables.
- [x] Implement liveness without external dependency checks.
- [x] Implement readiness with database connectivity and migration-state checks.
- [x] Configure SQLAlchemy async engine and session management.
- [x] Create the first schema migration.
- [x] Add JSON logging with request ID propagation.
- [x] Add a global exception handler using the error envelope.
- [x] Add Dockerfiles and Compose configuration.
- [x] Add developer commands through Make, Just, or task scripts.

### 6.3 Deterministic and Integration Tests

- [x] Test missing or malformed configuration.
- [x] Test liveness during database failure.
- [x] Test readiness during database failure.
- [x] Run migrations from an empty database.
- [x] Run migrations twice to verify idempotent startup behavior.
- [x] Test the API error envelope.
- [ ] Test graceful shutdown with an active request.

### 6.4 Behavioral Evaluation and Measurement

- [x] Record cold-start time and steady-state health-check latency.
- [x] Run the complete local setup from a clean checkout and record all manual steps that were unexpectedly required.

### 6.5 Documentation and Cleanup

- [ ] Update the architecture diagram if boundaries changed.
- [x] Add or revise Architecture Decision Records for consequential choices.
- [x] Update API or CLI documentation.
- [x] Add a migration or upgrade note when persistent data changed.
- [x] Record known limitations and deferred work.
- [ ] Complete the milestone retrospective template.
- [x] Prepare a clean-checkout demo script.
- [ ] Tag the release only after the exit gate passes.

## 7. Acceptance Criteria

- [x] One documented command starts API and PostgreSQL.
- [x] One documented command runs all local checks.
- [x] CI performs the same lint, type, test, and migration checks.
- [x] No secret or local credential is committed.
- [x] Liveness and readiness have distinct behavior.
- [x] Application startup and shutdown are graceful.
- [x] A clean environment can apply all migrations successfully.

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

- [x] `docs/learning/00-foundation.md`
- [x] `docs/adr/0001-package-and-project-structure.md`
- [ ] CI run link or screenshot
- [x] clean-checkout demo transcript
- [ ] tag `contextwise-v0.0-foundation`

Also attach or link:

- [ ] one successful trace;
- [ ] one representative failure trace;
- [ ] benchmark or evaluation output;
- [x] release notes describing user-visible and architectural changes;
- [x] open issues for consciously deferred work.

## 10. Suggested Demo Script

1. Clone the repository into an empty directory.
2. Start the stack.
3. Show liveness and readiness.
4. Stop PostgreSQL and demonstrate readiness failure while liveness remains healthy.
5. Run tests and migrations.


## 11. Reflection Questions

- Which bugs did typing prevent?
- What belongs in startup checks versus readiness checks?
- Where did async code add complexity without benefit?

Write answers in the learning note. The point is not to produce polished theory. The point is to record what your implementation taught you that documentation alone did not.

## 12. Exit Gate

Before starting Milestone 1, verify:

- [x] All required deliverables are complete or explicitly removed through an ADR.
- [x] All acceptance criteria pass.
- [ ] Required tests pass locally and in CI.
- [ ] The behavioral evaluation has a stored baseline.
- [x] The demo works from a clean environment.
- [ ] Security and privacy review is complete.
- [ ] The learning note and retrospective are committed.
- [ ] The release tag exists and points to the evaluated commit.

**Decision:** `IMPLEMENTED LOCALLY — EXIT GATE OPEN` — the foundation and local checks are complete, but the startup/shutdown lifecycle diagram, graceful-shutdown test, formal retrospective, CI/evaluation evidence, security/privacy review, and release tag remain outstanding.

A “pass with documented debt” is acceptable only for non-critical scope. It is not acceptable for data isolation, authorization, citation integrity, destructive actions, secrets, or unrecoverable migrations.
