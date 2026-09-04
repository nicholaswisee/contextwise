# Milestone 1 — LLM Gateway Demo

Start PostgreSQL and the API:

```bash
make up
```

Generate a free-form fake-provider result:

```bash
curl -sS http://127.0.0.1:8000/v1/generations \
  -H 'content-type: application/json' \
  -d '{"prompt":"Explain provider neutrality."}'
```

Generate validated structured output:

```bash
curl -sS http://127.0.0.1:8000/v1/generations \
  -H 'content-type: application/json' \
  -d '{"prompt":"Return an answer.","response_schema":"answer"}'
```

Stream a response:

```bash
curl -N http://127.0.0.1:8000/v1/generations/stream \
  -H 'content-type: application/json' \
  -d '{"prompt":"Stream a response."}'
```

Inspect supported configuration and a returned invocation ID:

```bash
curl -sS http://127.0.0.1:8000/v1/models
curl -sS http://127.0.0.1:8000/v1/prompts
curl -sS http://127.0.0.1:8000/v1/invocations/INVOCATION_ID
```

Stop the stack when finished:

```bash
make down
```
