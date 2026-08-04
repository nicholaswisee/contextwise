# Contextwise — Prerequisites and Toolchain

What you need installed before starting development, and how to verify it. This is the reference for Milestone 0's "clean checkout" requirement: a fresh machine following this document plus the milestone instructions should be able to start the full local stack.

## Required Toolchain

| Tool | Minimum | Verified on dev machine | Why it's needed |
|---|---|---|---|
| git | 2.40+ | 2.55.0 | Version control; the milestone workflow is commit/tag-driven |
| Python | 3.12+ | 3.14.6 | Application runtime |
| uv | 0.5+ | 0.12.1 | Package manager, virtualenvs, and pinned Python version. **Chosen over Poetry per ADR-0001.** |
| Docker Engine | 24+ | 29.7.1 | Runs PostgreSQL and later services (MinIO, Redis, Langfuse) |
| Docker Compose | v2 | 5.4.0 | One-command local stack |
| make | 4.0+ | 4.4.1 | Developer command runner (test/lint/up) — see Milestone 0 §6.2 |

Optional but useful:

| Tool | Version on dev machine | Why |
|---|---|---|
| psql | 18.4 | Manual database inspection during development |
| just | not installed | Alternative command runner if you prefer it over make |

`just` is a strict alternative to `make` — install only if you decide you dislike Make. It is not required.

## Verify the Environment

Run these to confirm the toolchain works:

```bash
git --version
python3 --version          # 3.12+
uv --version               # 0.5+
docker --version
docker compose version
make --version
```

If any are missing, install them first. The milestone instructions assume all of the above are present.

## Python Version Management

The application pins its interpreter through uv (`.python-version` + `pyproject.toml` `requires-python`), so the system Python is only a bootstrap. When Milestone 0 creates the project, `uv sync` will install and use the pinned version automatically. Current dev machine: Python 3.14.6.

## External Services and Keys

| When | What | Notes |
|---|---|---|
| Milestone 0 | PostgreSQL via Docker Compose | No credentials to obtain; Compose provides them locally |
| Milestone 1+ | LLM provider API key(s) | Loaded from `.env` via Pydantic Settings. **Never commit a key.** The gateway uses LiteLLM, so any provider key works (OpenAI, Anthropic, …) |
| Milestone 12+ | Ollama (local models) | Optional; only when you reach local inference |
| Milestone 3+ | Object storage | Local filesystem first, MinIO/R2 later — no account needed to start |

## Networking Note

FastAPI/uvicorn binds locally and PostgreSQL runs in Docker with a published port. No inbound internet access is required beyond the LLM provider API calls that begin in Milestone 1.
