# Milestone 2 — Conversation Domain

```mermaid
flowchart LR
    O[Owner token boundary\nowner_id = local]
    O --> C[Conversation]
    C --> M[Immutable message ancestry\nparent_id + sequence]
    M --> R[Conversation request\nunique conversation/key]
    R --> I[Model invocation\nprovider lifecycle]
    I --> S[Persisted context snapshot\nprompt/model/settings/messages/IDs]

    M --> B[Branch conversation\nsource conversation/message IDs]
    B --> BM[Copied ancestry\nnew message IDs]
    BM --> M
    R --> A[Streaming assistant placeholder]
    A --> I
```

## Data flow

1. The owner token is checked before any conversation lookup.
2. A conversation request locks the owned conversation, claims its unique
   idempotency key, and creates the user message plus streaming assistant
   placeholder in one transaction.
3. The service resolves the immutable system prompt, walks the selected parent
   chain, and applies deterministic budgeting.
4. The invocation snapshot is persisted before `GenerationService` opens the
   provider stream.
5. Text chunks update the existing assistant message. Completion, failure, and
   cancellation update both the message and request lifecycle records.
6. Context inspection reads the stored invocation snapshot rather than
   rebuilding context from current registry values.

## Boundaries

The current slice intentionally excludes retrieval, long-term memory,
document/file ingestion, provider-native multimodal requests, queues, and
multi-user authentication. The message-part schema is ready for later work,
but unsupported non-text parts cannot reach the text-only provider request.
