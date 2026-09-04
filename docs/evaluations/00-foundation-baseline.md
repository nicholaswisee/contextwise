# Milestone 0 — Foundation Baseline

**Measured:** 2026-09-04

## Environment

- Python 3.12.13
- Docker Compose PostgreSQL 16 Alpine
- API started with `make up`
- Measurements taken against `http://127.0.0.1:8000`

## Quality checks

```text
make check: passed
20 non-integration tests passed
ruff check: passed
ruff format: passed
mypy: passed
```

The integration suite also passed:

```text
3 integration tests passed
```

## Runtime measurements

The full Docker stack took **17,333 ms** from `make up` invocation until `/health/ready` first returned successfully. This includes container startup, dependency installation on the current image, migration startup, and API startup.

Ten steady-state `/health/ready` requests returned in **1.785–4.045 ms**, with a median of **3.044 ms**.

## Behavioral evidence

With PostgreSQL running:

```text
GET /health/live  -> 200 {"status":"alive"}
GET /health/ready -> 200 {"status":"ready"}
```

After `docker compose stop postgres`:

```text
GET /health/live  -> 200 {"status":"alive"}
GET /health/ready -> 503 {"detail":{"status":"not ready"}}
```

Every response included an `x-request-id` header.

## Limitations

- This is a deterministic service baseline, not an LLM quality benchmark.
- The startup measurement is machine- and image-cache-dependent.
- No remote GitHub Actions run was recorded in this local evaluation.
