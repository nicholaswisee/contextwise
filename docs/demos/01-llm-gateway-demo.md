# Milestone 1 — LLM Gateway Demo

Start PostgreSQL and the API:

```bash
export CONTEXTWISE_OWNER_TOKEN='set outside source control'
make up
```

Generate a free-form fake-provider result:

```bash
curl -sS http://127.0.0.1:8000/v1/generations \
  -H "X-Contextwise-Owner: ${CONTEXTWISE_OWNER_TOKEN}" \
  -H 'content-type: application/json' \
  -d '{"prompt":"Explain provider neutrality."}'
```

Generate validated structured output:

```bash
curl -sS http://127.0.0.1:8000/v1/generations \
  -H "X-Contextwise-Owner: ${CONTEXTWISE_OWNER_TOKEN}" \
  -H 'content-type: application/json' \
  -d '{"prompt":"Return an answer.","response_schema":"answer"}'
```

Stream a response:

```bash
curl -N http://127.0.0.1:8000/v1/generations/stream \
  -H "X-Contextwise-Owner: ${CONTEXTWISE_OWNER_TOKEN}" \
  -H 'content-type: application/json' \
  -d '{"prompt":"Stream a response."}'
```

Inspect supported configuration and a returned invocation ID:

```bash
curl -sS http://127.0.0.1:8000/v1/models -H "X-Contextwise-Owner: ${CONTEXTWISE_OWNER_TOKEN}"
curl -sS http://127.0.0.1:8000/v1/prompts -H "X-Contextwise-Owner: ${CONTEXTWISE_OWNER_TOKEN}"
curl -sS http://127.0.0.1:8000/v1/invocations/INVOCATION_ID -H "X-Contextwise-Owner: ${CONTEXTWISE_OWNER_TOKEN}"
```

Stop the stack when finished:

```bash
make down
```
