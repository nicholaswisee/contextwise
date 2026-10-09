# Milestone 4 — Clean Checkout RAG Demo

From a clean checkout with Docker, uv, and make installed:

```bash
uv sync
export CONTEXTWISE_OWNER_TOKEN='set a unique local value outside source control'
make up
uv run python scripts/smoke_milestone_4.py
make down
```

The script waits for the live API, uploads a Markdown document, waits for
ingestion, creates a collection, indexes it, asks a supported question, opens
its citation, reads the persisted run, asks an unsupported question, and
inspects retrieval-only output with `top_k=1`. A successful run prints
`PASS M4` and the collection, index, and run IDs. No cloud API key is needed.
Use `CONTEXTWISE_BASE_URL` if the API is not at `http://127.0.0.1:8000`.
Set `CONTEXTWISE_RAG_TRACE_PATH` to export the successful answer, opened
citation, insufficient-evidence response, retrieval-only response, and run.

## API routes

Every route requires `X-Contextwise-Owner`.

| Route | Purpose |
|---|---|
| `POST /v1/rag/collections` | Create a named owned collection |
| `GET /v1/rag/collections` | List owned collections and active index IDs |
| `PUT /v1/rag/collections/{id}/documents/{document_id}` | Add an owned document; invalidates active index |
| `POST /v1/rag/collections/{id}/indexes` | Build a new index from latest completed versions |
| `POST /v1/rag/collections/{id}/retrieve` | Ranked evidence without generation |
| `POST /v1/rag/collections/{id}/ask` | Cited answer or abstention |
| `GET /v1/rag/runs/{run_id}` | Query, config, index version, candidates, selected IDs, status |
| `GET /v1/rag/evidence/{chunk_id}` | Open a stored passage with source metadata |

Index body: `{"chunk":{"size":40,"overlap":4,"strategy":"heading"}}`.
`strategy` is `fixed` or `heading`. Optionally set `embedding_model` to the
configured cloud model or deterministic `hash-256-v1`/`hash-256-v2`.

Query body: `{"query":"...","config":{"top_k":5,"min_score":0.25,
"context_tokens":400,"query_rewrite":false}}`. The ask route defaults to
`generation_model:"extractive"`. A registered gateway model can be named
explicitly; an invalid citation makes its answer abstain. `min_score` is a
cosine ranking threshold, not a probability. Evidence citation labels `[E1]`
are local to one response; use the evidence object's `id` for the lookup URL.

The demo uses deterministic lexical embeddings and an extractive answer.
Run `make test-integration` and the frozen
[`50-case evaluation`](../evaluations/04-rag-report.md) for database and
behavioral evidence. Migration `0005` requires pgvector on PostgreSQL 16.
