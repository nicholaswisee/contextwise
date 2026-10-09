# Milestone 4 — Retrieval Security and Failure Review

**Scope:** Local single-owner service. Owner token authentication remains the
outer API boundary.

## Checked boundaries

- Collection creation, membership, indexing, retrieval, run reads, and
  citation reads all require the owner token. Membership accepts only a
  document whose `owner_id` matches the collection owner. Retrieval pins one
  owner-scoped collection index. A guessed chunk or run ID from another owner
  returns 404. The integration test exercises these cases.
- A new index publishes in one transaction. Failed embedding batches cannot
  partially replace the active index. Old citations remain available after
  reindexing, and a new member clears the active pointer.
- Query input, top-k, score, context budget, chunk size, and overlap are
  bounded by validation. Indexing caps a collection at 5,000 chunks. The
  cloud adapter bounds batch size, timeout, and retries.
- Stored passages are treated as data in the gateway prompt. Citation IDs are
  checked against selected evidence before an LLM answer is returned. The
  default extractive answer quotes stored text directly.
- API errors do not include embedding response bodies or the API key.

## Failure behavior

| Failure | Result |
|---|---|
| Empty or unindexed collection | Empty retrieval; ask abstains |
| Member has no completed version | Index request returns 409 |
| Membership changes during build | Publish rejects with 409 |
| Cloud embedding batch fails | Index remains on previous active version |
| Vector count, dimensions, or values invalid | Index request fails before publication |
| Unknown generated citation | Answer rejected as `invalid_citation` |
| Other owner requests run or passage | 404 |

## Residual limits

The synchronous index endpoint can consume CPU, database, and paid cloud
embedding quota before the chunk cap is checked; rate limits and a durable
index job are needed for public multi-user use. Query and selected evidence
are persisted in retrieval runs without a retention policy. If configured,
cloud embedding sends document content and questions to the configured
provider; gateway generation sends selected passages and the question.
Operators must choose providers consistent with their data policy. The
whitespace context budget is approximate. Citation validation only checks
reference integrity, so a gateway answer with valid labels is explicitly
qualified as unverified; the default extractive mode gives a narrower
guarantee. Prompt
injection in documents still requires broader adversarial evaluation. These
limits are tracked as CW-09 through CW-12.
