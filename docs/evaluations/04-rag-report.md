# Milestone 4 Retrieval Baseline

**Dataset:** [`datasets/retrieval/v1/cases.json`](../../datasets/retrieval/v1/cases.json)
**Raw run:** [`04-rag-baseline.json`](04-rag-baseline.json)
**Runner:** [`scripts/run_rag_eval.py`](../../scripts/run_rag_eval.py)

The frozen set has 50 labeled questions over five synthetic Markdown
documents, ten facts per document. Each case has an exact expected answer and
source statement. The runner uploads and indexes through the public API,
queries PostgreSQL/pgvector, then opens each cited chunk through the public
citation route. Recall@k requires a candidate from the labeled document that
contains the expected answer. Answer support requires the expected answer in
an extractive quote that occurs in selected evidence. Citation validity
requires an answered quote to resolve to a stored passage. Latency is the
service-recorded request time; cost is zero because this run uses local
embeddings and extractive generation.

| Setting | Chunks | Recall@k | Answer support | Citation validity | Mean latency |
|---|---:|---:|---:|---:|---:|
| Baseline: 24 tokens, overlap 4, k=5 | 20 | 100% | 92% | 100% | 7.84 ms |
| Short: 16 tokens | 30 | 98% | 86% | 100% | 6.20 ms |
| Long: 40 tokens | 15 | 100% | 100% | 100% | 8.30 ms |
| No overlap | 20 | 96% | 86% | 100% | 7.16 ms |
| Top one | 20 | 78% | 78% | 100% | 5.32 ms |
| Heading aware | 20 | 100% | 92% | 100% | 5.86 ms |
| Query rewrite | 20 | 100% | 92% | 100% | 5.68 ms |
| Hash embedding v2 | 20 | 100% | 92% | 100% | 6.14 ms |

The initial baseline missed four answers even though the relevant passage
was retrieved: Birch lab goggles, Coral harbor flag, Coral harbor inspection,
and Ember theater props. The sentence selector favored another sentence in a
multi-fact chunk. Short chunks and no overlap additionally split answer terms
away from useful query terms. Top one lost eleven relevant passages that were
present in the top five. Heading prefix and the narrow rewrite rule did not
improve this synthetic set. The 40-token setting covered all 50 facts here;
it is the product default, but this is too small and too formulaic a corpus to
claim general superiority. Hash v2 is a second deterministic projection, not
a different semantic provider.

**Failure taxonomy:** ingestion/provenance 0 observed; chunk boundary 1–2
cases in short/no-overlap variants; retrieval ranking 11 top-one cases;
context selection/generation 4 baseline cases; citation resolution 0. These
counts overlap across variants and are not independent incidents. The full
per-question record includes run IDs and statuses for debugging.

**Limits:** No credentialed cloud embedding or LLM quality measurement was
performed. The questions use phrasing close to their source statements, so
the baseline does not test robust paraphrase understanding, adversarial
content, large collections, multilingual text, or real PDF layout. These are
follow-ups in the deferred work register. A score threshold is not a calibrated
confidence level.
