# Milestone 3 Learning Note — Document Ingestion

## What changed in the mental model

An upload is acceptance of original bytes and a durable job, not proof that a
parser succeeded. The API returns `202` with version and job IDs; status and
stable failure codes are queryable. The worker can restart because the database
lease is the source of truth.

Normalization damages provenance when offsets are computed after whitespace is
collapsed. This implementation records offsets in the raw decoded file or PDF
page extraction, then stores normalized display text. The source slice can be
checked against the normalized passage in the frozen fixture runner.

Deduplication belongs after byte hashing and before version creation, inside a
transaction protected by the document row lock. The local object store also
deduplicates by digest. This keeps repeated uploads from creating another
version or set of segments while allowing a changed same-name upload to become
version 2.

The transaction boundary is the state transition and its related rows:
claim plus attempt and lease; completion plus replacement segments and full
text; failure plus stable code; retry plus pending state. Parsing stays outside
the transaction so a slow parser does not hold a database lock. A stale worker
cannot overwrite a newer attempt.

PDF page extraction is not OCR. The 15-document baseline proves the current
parser and location contract on small text-based fixtures. It does not claim
correct extraction from scans or complex tables.
