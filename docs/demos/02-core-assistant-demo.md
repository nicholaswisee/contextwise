# Milestone 2 Core Assistant Demo

Run from a clean checkout with PostgreSQL available:

```bash
uv sync
export CONTEXTWISE_OWNER_TOKEN='set outside source control'
make up
make migrate
export OWNER_HEADER="X-Contextwise-Owner: ${CONTEXTWISE_OWNER_TOKEN}"

CONVERSATION_ID=$(curl -fsS -X POST http://localhost:8000/v1/conversations \
  -H "$OWNER_HEADER" | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')

curl -N -X POST "http://localhost:8000/v1/conversations/${CONVERSATION_ID}/messages/stream" \
  -H "$OWNER_HEADER" -H 'Idempotency-Key: demo-turn-1' \
  -H 'Content-Type: application/json' \
  --data '{"parts":[{"type":"text","text":"My name is Ada."}]}'

# Copy the completed message ID from the SSE completed event.
curl -fsS "http://localhost:8000/v1/conversations/${CONVERSATION_ID}/context/${MESSAGE_ID}" \
  -H "$OWNER_HEADER"

curl -N -X POST "http://localhost:8000/v1/messages/${MESSAGE_ID}/regenerate/stream" \
  -H "$OWNER_HEADER" -H 'Idempotency-Key: demo-regenerate-1'

curl -fsS -X POST "http://localhost:8000/v1/messages/${MESSAGE_ID}/branch" \
  -H "$OWNER_HEADER"

make down
```

## Expected evidence

- conversation creation returns an `id`;
- the terminal SSE event contains `conversation_id`, `message_id`, and
  `invocation_id`;
- context inspection returns the persisted prompt/model metadata, provider
  message snapshot, selected IDs, estimate, and truncation flag;
- regeneration returns a different assistant message ID;
- branching returns a new conversation ID.

The local fake provider demonstrates lifecycle plumbing only. It is not a
credentialed model-quality claim.
