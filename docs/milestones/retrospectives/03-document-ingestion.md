# Contextwise Milestone Retrospective

**Milestone:** 3 — Document Ingestion Pipeline
**Date:** 2026-10-09
**Release tag:** `contextwise-v0.3-ingestion`.
**Commit evaluated:** `c1542df` on `milestone-2-3-continuation`.

## 1. What Was Built

The API accepts owner-scoped TXT, Markdown, and PDF uploads, stores original
bytes by hash, creates stable documents and versions, and processes durable
jobs. It exposes status, failure codes, retry, reprocess, cancellation, full
extracted text, and source segments with page, section, and character offsets.

## 2. Baseline and Result

The frozen `parser-fixtures-001` run has 15 small documents, with 15 complete
extractions and 15 accurate source locations. Local integration tests exercise
PostgreSQL queue behavior and the public API. The live Docker smoke demo
covers all supported upload types and failure recovery.
[Remote CI](https://github.com/nicholaswisee/contextwise/actions/runs/37859902740)
passed check, migration, and integration jobs on `c1542df`.

## 3. Important Failures and Corrections

- The initial Markdown paragraph matcher swallowed text after a heading;
  line-based section parsing and an offset regression test corrected it.
- The first Docker smoke attempt reached the container before API startup;
  the smoke script now waits for `/health/ready`.
- The Docker entrypoint's plain `uv run` installed development dependencies;
  production startup now uses `uv run --no-dev`.
- The test Compose file reused the main stack's project name and replaced its
  PostgreSQL container. It now has a distinct project name, and the integration
  test target always tears it down after the run.

## 4. Architecture and Security

ADR-0003 records filename identity, version hashes, object storage, leased jobs,
and source-offset policy. The local review covers owner checks, upload limits,
path safety, parser failure codes, lease replay, and remaining PDF isolation
work. The object store has no garbage collection or retention API yet.

## 5. Deferred Work

- Process isolation for hostile PDFs and OCR/table extraction are later
  hardening and retrieval work.
- Cloud object storage, cleanup of orphaned objects, and retention controls
  remain follow-up operations work.
- The release gate is closed on the evaluated M3 revision. Public upload still
  requires the PDF process, body-size, and retention follow-ups.

Tracked as CW-05 through CW-08 in `docs/issues/README.md`; release-gate work
remains on the milestone checklist.

## 6. Exit Decision

`PASS WITH DOCUMENTED DEBT`. The behavior, deterministic tests, fixture
baseline, local review, live demo, and remote CI pass. The tag
`contextwise-v0.3-ingestion` marks the documentation-only gate closure on top
of the evaluated revision. The remaining debt is recorded as CW-05 through
CW-08 and does not weaken local authorization or provenance requirements.
