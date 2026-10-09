# Milestone 4 — What Manual RAG Exposed

The pipeline begins with an explicit collection. An index snapshots completed
document versions, chunks each stored segment, embeds the chunks, and
atomically publishes a new version. Retrieval embeds the query with that
index's model and asks pgvector for cosine-nearest chunks. The answer builder
then selects evidence under a token budget and adds labels that can be opened
through an owner-scoped passage endpoint. The run record keeps enough IDs and
scores to inspect retrieval without invoking generation.

The frozen 50-question run separated two failure types that a single answer
score would hide. The first top-five retrieval had 100% passage recall but
only 92% expected-answer support. Four selected passages contained the right
answer while the extractive selector quoted another sentence. Reducing top-k
to one dropped passage recall to 78%, so those misses occurred in retrieval
ranking. The chunk-size and overlap variants exposed boundary splits. No
citation failed to resolve in the baseline.

The local hash embedding is useful because every run is reproducible and
free of API cost. It mostly measures shared vocabulary, not semantic
paraphrase. A cosine score is an angle-derived ranking signal. The 0.1 floor
used in evaluation is not a 10% relevance probability and should not be
presented as confidence. A cloud adapter exists, but a provider-specific
benchmark needs credentials and a separate frozen run.

Heading-aware chunking adds the stored Markdown section to embedding input
without changing the cited passage. It tied fixed chunking on this dataset
because each document already repeated its subject name. Long chunks won on
these short synthetic documents; real manuals may behave differently because
larger chunks can blend unrelated facts. The default is 40 words with four
words overlap until a broader corpus gives better evidence.

The provenance distinction matters: ingestion's `start_offset` and
`end_offset` locate the original extracted segment. Chunk offsets locate text
inside the normalized segment. Concatenating those numbers would create an
incorrect raw-file location after whitespace normalization. A citation opens
the stored chunk and reports both ranges separately.

The answer path abstains when retrieval or lexical evidence is insufficient.
An explicitly requested gateway model must cite a selected label, but label
validation alone cannot judge claim support. The extractive default avoids
that gap for its quoted statement at the cost of synthesis and paraphrase.
