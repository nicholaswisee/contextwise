# Milestone 2 — Core Assistant Security Review

**Review status:** Local security and privacy review complete for the single-owner service
**Date:** 2026-10-09

## Scope

- owner-protected conversation REST/SSE routes;
- PostgreSQL conversation, message, request, and invocation persistence;
- context inspection and branch provenance;
- message parts and unsupported multimodal behavior;
- streaming retry, timeout, failure, and cancellation handling.

## Controls verified

1. `X-Contextwise-Owner` is required and compared against the configured token.
   Missing or invalid credentials return `401` before resource handling.
2. Repository reads and writes use the fixed owner ID, and missing or unowned
   conversations/messages are not returned through the authorized service.
3. The idempotency key is unique per conversation. Completed terminal requests
   replay, active requests return `409`, and a changed fingerprint returns
   `422`.
4. The accepted request and assistant placeholder are committed before provider
   iteration. Partial failures update the existing placeholder rather than
   creating a second assistant result.
5. Provider error messages are reduced to stable error codes. Credentials and
   raw provider payloads are not persisted.
6. Context inspection exposes the stored snapshot only after owner validation.
   It contains provider messages and selected IDs by design, so the endpoint is
   treated as sensitive owner data.
7. Image/file references are stored but rejected before the text-only
   `LLMRequest`; no local file contents are ingested.
8. The previous generation, invocation, and registry routes now require the
   same owner token. An unauthenticated generation request returns `401` before
   any provider work. Integration tests cover all four route groups.
9. Production settings reject the default development owner token, and Docker
   Compose requires an explicitly supplied token before starting the API.

## Observed traces

- Successful fake-provider trace: durable request claim → streamed `chunk` →
  `completed` with conversation, message, and invocation identifiers.
- Representative failure trace: durable request claim → streamed partial chunk
  → provider timeout → terminal `error(code=timeout)` on the same assistant
  placeholder.

These traces are covered by the assistant service and API integration tests;
they do not contain credentials or raw provider error payloads.

## Retention and operational limits

Conversation content and context snapshots are durable application data. M2
does not add automatic deletion or redaction of user content; deployment
operators must define retention before using non-local data. The provider
timeout remains configured by the existing LLM settings, the context budget is
bounded at 4096 estimated tokens, and no background queue was introduced.

## Remaining risks

- The default local token is intentionally suitable only for local development;
  operators must set `CONTEXTWISE_OWNER_TOKEN` outside source control.
- A single shared token cannot provide multi-user isolation or rotation policy.
- Character estimates can differ from provider tokenization.
- The review covers this local single-owner surface. External deployment,
  multi-user identity, rotation, and real-provider budget enforcement require
  separate work. Milestone 1's remote CI and credentialed measurement debt is
  not silently marked complete.

## Decision

`LOCAL REVIEW COMPLETE`. The review method was source inspection of every
public route and owner-scoped repository query, targeted authorization and
redaction tests, migration review, and the live Docker smoke demo. No critical
data-isolation or secret-disclosure finding remains in the local scope. This
does not substitute for a production deployment review.
