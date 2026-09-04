# Contextwise Milestone Retrospective

**Milestone:** 0 — Engineering Foundation
**Release tag:** Not applicable; release tagging is not required for this project.
**Date completed:** 2026-09-04
**Commit evaluated:** Working tree verified after `e60c1c6` and the Milestone 0 completion changes.

## 1. What Was Built

The project now has a reproducible FastAPI service with uv packaging, typed Pydantic settings, async SQLAlchemy database access, Alembic migrations, Docker Compose, JSON logging, request IDs, liveness/readiness endpoints, and CI configuration.

## 2. What Was Learned

- Application factories make FastAPI startup configuration testable.
- Lifespan code is the correct place to initialize and dispose shared resources.
- Liveness and readiness answer different operational questions.
- Async database access requires explicit engine and session lifecycle management.
- A local `.env` can invalidate a configuration test unless the test isolates both process and dotenv input.

## 3. Baseline and Result

- Baseline configuration: no previous runnable service baseline.
- Candidate configuration: FastAPI + PostgreSQL foundation, verified through Docker Compose.
- Dataset/version: deterministic health and migration checks; no probabilistic dataset.
- Quality result: 20 non-integration tests and 3 integration tests passed.
- Latency result: 1.785–4.045 ms steady-state readiness latency; 3.044 ms median.
- Cost result: no external provider calls or API keys required.
- Failure-rate result: readiness correctly returned `503` when PostgreSQL was stopped; liveness remained `200`.

## 4. Important Failures

### Local dotenv contaminated a missing-setting test

- Symptom: `make check` failed because `Settings()` did not raise when `DATABASE_URL` was expected to be absent.
- Root cause: the local `.env` supplied `DATABASE_URL`.
- Evidence: the test passed after deleting the environment variable and disabling dotenv loading for that assertion.
- Fix: isolated the test; production settings continue loading `.env`.
- Regression test: `test_settings_require_database_url`.

### Shutdown disposed resources before an active request finished

- Symptom: the lifespan shutdown path completed while a deliberately blocked request was still running.
- Root cause: shutdown called `database.close()` immediately after `yield` without tracking active requests.
- Evidence: the new shutdown test failed before the fix and passed afterward.
- Fix: middleware tracks active requests and lifespan waits for the count to reach zero.
- Regression test: `test_shutdown_waits_for_active_request`.

### Container running did not mean API ready

- Symptom: an immediate request after `make up` could arrive before the API had finished startup migration work.
- Root cause: the Compose API service has no container healthcheck; `--wait` does not establish endpoint readiness for this service.
- Deferred action: add an API healthcheck when startup behavior or deployment orchestration requires it.

## 5. Architecture Decisions

- Decisions accepted: uv; src layout; FastAPI factory; layered API/application/infrastructure packages; async SQLAlchemy; separate liveness/readiness checks.
- Alternatives rejected: Poetry; coupling route handlers directly to database setup; treating database connectivity as liveness.
- New coupling introduced: `RequestIDMiddleware` now uses shared `AppState` request tracking for graceful shutdown.
- Exit strategy: replace the simple in-process state tracker with a server-managed lifecycle or richer worker coordination if deployment concurrency requires it.

## 6. Security and Privacy Review

See [`docs/security/00-foundation-review.md`](../../security/00-foundation-review.md). The current surface has no user-data or tool execution path. The full team-mode security audit remains outstanding because team mode was unavailable.

## 7. Operational Review

- New traces or metrics: none; JSON logs and request IDs are present.
- Most expensive path: container startup and migration initialization.
- Slowest path: cold stack startup at 17.333 seconds in the recorded run.
- Most common error: readiness failure when PostgreSQL is unavailable.
- Recovery behavior: liveness remains available, readiness recovers after PostgreSQL restarts, and shutdown waits for active requests.

## 8. Demonstration

See [`docs/demos/00-foundation-demo.md`](../../demos/00-foundation-demo.md) and [`docs/evaluations/00-foundation-baseline.md`](../../evaluations/00-foundation-baseline.md).

## 9. Deferred Work

- Add an API container healthcheck if Compose readiness needs to wait on HTTP availability.
- Run the full team-mode security review.
- Record a remote CI run if CI evidence is required for the milestone gate.
- Add tracing and metrics in a later observability milestone.

## 10. Exit Decision

`PASS WITH DOCUMENTED DEBT`

The foundation is implemented and locally verified. The project does not require a release tag, but the remote CI evidence and full security review remain documented follow-up items rather than being represented as complete.
