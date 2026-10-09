# Milestone 3 — Clean Checkout Ingestion Demo

From a clean checkout with Docker, uv, and make installed:

```bash
uv sync
export CONTEXTWISE_OWNER_TOKEN='set a unique local value outside source control'
make up
uv run python scripts/smoke_milestones_2_3.py
make down
```

The script waits for readiness, then exercises the owner gate, two-turn chat,
context inspection, regeneration, and branching. It uploads TXT, Markdown,
and PDF, waits for processing, checks passage provenance, repeats an upload,
forces a PDF parser failure, and retries the failed job. Set
`CONTEXTWISE_DEMO_EXPORT_PATH` and `CONTEXTWISE_INGESTION_TRACE_PATH` to write
fresh synthetic traces without credentials. A successful run prints two `PASS`
lines.

The smoke demo uses the local fake model and simple generated PDF. It verifies
the public interface and persistence lifecycle, not model answer quality or
OCR. `make test-integration` separately checks lease expiry and retry
behavior against PostgreSQL.

## API routes

| Route | Purpose |
|---|---|
| `POST /v1/documents` | Multipart upload; returns document, version, and job IDs |
| `GET /v1/documents` | List owned documents |
| `GET /v1/documents/{id}` | Show versions for one owned document |
| `GET /v1/document-versions/{id}` | Show status, text, segments, and latest job |
| `GET /v1/ingestion-jobs/{id}` | Inspect status, attempts, trace ID, and failure code |
| `POST /v1/ingestion-jobs/{id}/retry` | Retry a failed or cancelled job |
| `POST /v1/document-versions/{id}/reprocess` | Create a new processing job |
| `POST /v1/ingestion-jobs/{id}/cancel` | Cancel a pending or processing job |

Every route requires `X-Contextwise-Owner`. Uploads return `202`; invalid
files return `422`. `0004_document_ingestion` applies automatically in Docker
startup or through `make migrate` in a local Python environment. Its downgrade
removes document data, so export it before an intentional downgrade.
