# Milestone 0 — Engineering Foundation Learning Note

## What was built

A minimal FastAPI service with uv packaging, Pydantic settings, async SQLAlchemy + Alembic, structured JSON logging, request IDs, Docker Compose, and GitHub Actions CI.

## What worked

- uv resolved dependencies quickly and produced a clean `uv.lock`.
- FastAPI's `lifespan` and dependency injection made shutdown and database lifecycle testable.
- Separating liveness (no external deps) from readiness (DB + migrations) clarified startup semantics.
- Using `Annotated[Database, Depends(get_database)]` satisfied both FastAPI and ruff's B008 rule.

## What was hard

- Alembic async config works with `postgresql+asyncpg://` directly; the initial instinct to translate to a sync driver added a dependency that did not exist.
- Testing the app with a real database required a test-specific Docker Compose on a non-default port because the host already had PostgreSQL services.
- pytest-asyncio's session-scoped fixtures must not be `autouse` when they require external services; otherwise unit tests fail during collection.

## Open questions

- Should readiness also verify the latest migration revision matches `alembic heads`? For now it only checks connectivity.
- Is the global exception handler's envelope sufficient, or should it include request IDs and trace context?

## Decisions recorded

- ADR-0001: uv chosen over Poetry.
- Error envelope: `{error: string, message: string}` returned as JSON for unhandled 500s.
