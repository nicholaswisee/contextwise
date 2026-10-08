# ADR-0003: Durable Local Document Ingestion

**Status:** Accepted
**Date:** 2026-10-09
**Milestone:** 3 — Document Ingestion Pipeline

## Decision

Milestone 2 passed with documented, non-critical Milestone 1 predecessor debt.
Its assistant code, local tests, clean demo, remote CI, and release tag are
complete. Milestone 3 builds on that evaluated assistant revision.

One owner and exact filename identify a document. A SHA-256 digest identifies a
version within that document; a changed file with the same name creates the next
numbered version. Equal bytes under another filename create another document
record but share the content-addressed original object. An upload writes bytes
to the local object store before creating database rows. This can leave an
orphan object after a database failure; it cannot leave a version that points to
missing bytes after a successful response. Garbage collection is deferred.

PostgreSQL holds versions, extracted text, source segments, and ingestion jobs.
The object store holds original bytes under a validated digest path. The API
never returns an object-store path. Both document and job reads join through
`owner_id` after the owner token is checked.

A worker polls pending jobs and processing jobs with expired leases. It claims
one row using `FOR UPDATE SKIP LOCKED`, increments the attempt, and records a
lease. A late worker can only finish the attempt it claimed. A completed
reprocess creates a new job and replaces all segments in one transaction.
Retries reuse a failed or cancelled job with an incremented attempt. Client
uploads of identical bytes reuse the existing version and job.

The state machine is `pending → processing → completed | failed | cancelled`.
Failed and cancelled jobs may return to `pending`; completed versions may be
reprocessed through a new job. The original object and historical version ID
never change. `trace_id` links a job to the API request that created or retried
it; `attempts`, `error_code`, timestamps, and state are queryable.

TXT and Markdown are decoded as UTF-8. PDF uses pypdf and retains 1-based page
numbers. Segment offsets refer to the decoded original file or raw extracted
page text before normalization. Normalization only collapses whitespace in the
display text. Markdown headings set the section for subsequent passages.

## Limits and alternatives

- Uploads are at most 10 MiB by default. The API reads at most one byte over the
  limit after multipart parsing; TXT, Markdown, and PDF are the only supported
  types. A front-door body limit is required before public deployment because
  multipart parsing may spool data first.
- PDF extraction is limited to 200 pages and a 30-second application timeout.
  The Python thread may continue after timeout; isolation in a worker process
  is a later hardening step before accepting hostile PDFs at scale.
- PDF image OCR, password handling, and embedded attachments are out of scope.
- An external queue and cloud object store would add operations before the
  local provenance and retry contract is measured. The repository and object
  store are isolated so they can be replaced later.
- A relational segment table is used now; retrieval indexes begin in M4.

The [pypdf reader documentation](https://pypdf.readthedocs.io/en/stable/modules/PdfReader.html)
defines the `PdfReader` stream and encrypted-file interfaces used here.
