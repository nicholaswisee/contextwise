# Milestone 3 — Ingestion Security and Failure Review

**Status:** Local review complete for the single-owner local service
**Date:** 2026-10-09

## Checked boundaries

- All document, version, and job routes require the owner token. Repository
  reads join through the owner record, so another owner's ID is not enough to
  retrieve a file or job. The object path is never returned.
- Filename traversal, unknown extensions, MIME mismatches, binary TXT/Markdown,
  empty uploads, invalid PDF signatures, and files over the configured byte
  limit are rejected before database or parser work.
- The object key is a server-computed SHA-256 digest. Reads validate its shape
  and verify bytes against the digest; writes use a temporary file and atomic
  rename. Original bytes remain separate from extracted content.
- Worker errors are persisted as stable codes. Raw PDF exceptions and extracted
  content are not placed in error responses or routine logs.
- A lease and attempt number prevent an expired worker from replacing the
  result of a later attempt. Cancellation and retry are durable states.

## Failure matrix

| Failure | Result | Recovery |
|---|---|---|
| Corrupt or encrypted PDF | `failed` with stable code | Upload corrected bytes or retry |
| Empty extracted text | `failed: empty_document` | Upload corrected bytes |
| Parser timeout | `failed: parser_timeout` | Retry job |
| Worker process stops | Lease eventually expires | New worker claims job |
| Repeated upload | Existing version and job returned | No extra segments |
| Repeated delivery | Attempt guarded completion | No extra segments |
| Object missing or corrupt | `failed: object_unavailable` | Restore bytes and retry |

## Residual limits

The Python PDF parser runs in a thread; a timed-out parser thread cannot be
forcibly killed. The 10 MiB and 200-page limits bound common cases, but a
hostile compressed PDF still needs process isolation before a public
multi-user deployment. The local object store has no automatic garbage
collection or retention/deletion API. FastAPI's multipart parser may spool an
oversized body before the route's byte check runs; a network-level request-body
limit is required before public upload. These limits are tracked as CW-05,
CW-07, and CW-08. This is a local milestone boundary, not approval to accept
arbitrary internet uploads.
