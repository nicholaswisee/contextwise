# Contextwise

A production-grade, context-aware personal AI workspace — built as a solo learning project through deliberate, measurable milestones.

**One evolving application, not a collection of disconnected tutorials.** Contextwise starts as a provider-neutral LLM service and grows into a document assistant, research system, safe tool-using assistant, memory-enabled workspace, repository intelligence tool, MCP server, and experimentation platform.

## Repo Layout

| Path | Purpose |
|---|---|
| [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) | Product vision, tech strategy, scope boundaries |
| [`docs/README.md`](docs/README.md) | Milestone roadmap index (00–19) |
| [`docs/PREREQUISITES.md`](docs/PREREQUISITES.md) | Required toolchain and environment setup |
| [`docs/milestones/`](docs/milestones/) | Executable milestone work packages |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records |
| [`docs/MASTER_CHECKLIST.md`](docs/MASTER_CHECKLIST.md) | Progress tracking across milestones |

## Current Status

**Milestone 0 implementation is in place.** The local quality checks pass, but the milestone exit gate remains open for the documented evidence and follow-up work listed in the milestone file.

## Getting Started

1. Read [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) — the product vision and learning goals.
2. Verify the toolchain against [`docs/PREREQUISITES.md`](docs/PREREQUISITES.md).
3. Execute [Milestone 0 — Engineering Foundation](docs/milestones/00-engineering-foundation.md): the bootstrap that creates the reproducible Python service, health endpoints, PostgreSQL/Alembic setup, Docker Compose, and CI.
4. Complete milestones in order; do not begin the next until the previous exit gate has a recorded decision.

## Toolchain Summary

Python (managed by **uv**), uv for packaging, Docker Compose for the local stack, `make` for developer commands, FastAPI + PostgreSQL + SQLAlchemy + Alembic as the core service stack. Full details in [`docs/PREREQUISITES.md`](docs/PREREQUISITES.md).

## Working Rule

A milestone is complete only when the feature works, the tests pass, the evaluation evidence is stored, the system is observable, the risks are documented, and the exit gate is signed off.
