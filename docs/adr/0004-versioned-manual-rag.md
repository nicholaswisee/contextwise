# ADR-0004: Versioned Manual Dense Retrieval

**Status:** Accepted for the local single-owner slice
**Date:** 2026-10-09
**Milestone:** 4 — Manual Dense Retrieval and Cited RAG

## Decision

The user directed work into Milestone 4 while the Milestone 3 gate was still
open. The Milestone 3 gate was closed separately on its evaluated revision
before publishing Milestone 4 code. Milestone 4 does not change the Milestone 3
release tag.

An owner creates a named collection and explicitly adds owned documents.
Indexing selects each member's latest completed document version. It splits
each stored segment into whitespace-token windows, embeds the windows, and
publishes a new immutable index. The collection's active index pointer changes
in the same transaction as the new index and chunks. A query reads one index
ID and searches only its chunks. Historical chunks and citations remain
resolvable after reindexing. Adding a document clears the active pointer until
the collection is rebuilt. A newer document version does not silently alter
the active snapshot.

The chunk identity is `(index_id, segment_id, ordinal)`. Each chunk also stores
document/version IDs, the original segment's source offsets, normalized
segment-relative chunk offsets, page, section, text, embedding model through
the index, and a 256-dimensional vector. Original source offsets delimit the
whole segment because ingestion normalizes whitespace before chunking; the
chunk offsets delimit its normalized text. Neither is presented as an exact
raw-file byte range.

The default local embedding model is a deterministic 256-dimensional lexical
hash baseline. A separate OpenAI-compatible HTTP adapter batches requests,
asks for 256 dimensions, retries transport and 429/5xx responses, and rejects
wrong counts, dimensions, nonfinite values, and zero vectors. The provider
must support a 256-dimensional output. A credentialed cloud semantic baseline
is deferred; the local hash baseline is explicitly lexical and must not be
described as proof of semantic quality.

Cosine distance is computed by pgvector and converted to a score of
`1 - distance`. It is a ranking signal, not a probability of relevance.
`top_k` and `min_score` filter candidates; a whitespace-token budget selects
the evidence supplied to answer generation. Each result carries its stored
chunk UUID and a request-local `[E1]` citation label. The default extractive
answer quotes a sentence from selected evidence, cites its label, and abstains
when the query lacks enough lexical support. An explicitly selected gateway
model may synthesize an answer, but unrecognized or absent citations are
rejected as `invalid_citation`. Citation validation proves a reference points
to selected evidence; it does not prove every natural-language claim is true.

Every retrieval request persists owner, collection, original and effective
query, config, index ID and number, ranked candidate IDs/scores, selected
chunk IDs, answer/status, latency, and cost estimate. Retrieval-only requests
persist the same trace. The API exposes owner-scoped run and evidence reads.

## Alternatives and limits

- The index is rebuilt synchronously for at most 5,000 chunks. A durable index
  job and incremental publication are deferred until scale or reliability
  measurements justify them.
- Chunking stays inside one source segment so a citation has one page/section
  and one provenance range. This can lose context across paragraph boundaries.
- The HNSW cosine index speeds larger collections; approximate search can
  miss neighbors. The frozen benchmark measures the full retrieval pipeline.
- Context tokens are approximated by whitespace words plus label overhead.
  A model-specific tokenizer is needed before strict provider context limits.
- The default extractive answer is intentionally narrow. It cannot combine
  facts across passages and may abstain on paraphrased questions.
- Collection membership is checked again before publication. A version
  uploaded during a build may require another index request to become active.

[pgvector's project documentation](https://github.com/pgvector/pgvector)
specifies the cosine operator and HNSW index. The
[pgvector Python adapter](https://github.com/pgvector/pgvector-python)
documents its SQLAlchemy vector type and cosine-distance expression.
