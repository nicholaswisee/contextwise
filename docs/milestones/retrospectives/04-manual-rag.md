# Contextwise Milestone Retrospective

**Milestone:** 4 — Manual Dense Retrieval and Cited RAG
**Date:** 2026-10-09
**Release tag:** Pending exit gate.

## Built

Versioned collection indexes, two chunking modes, local and cloud embedding
adapters, pgvector cosine search, evidence objects, budgeted context,
extractive and gateway cited answers, retrieval-only and full answer routes,
openable citations, and durable retrieval traces.

## Measured

The frozen 50-case, five-document local benchmark tested eight configurations.
The initial 24-word baseline reached 100% Recall@5, 92% expected-answer
support, and 100% citation resolution. A 40-word setting reached 100% on all
three in this synthetic set. The top-one experiment fell to 78% recall. The
raw run and failure taxonomy are in `docs/evaluations/04-rag-baseline.json`
and `docs/evaluations/04-rag-report.md`.

## Corrections

The first answer mode quoted the whole top chunk and supported only 39 of 50
expected answers. A sentence selector raised the initial baseline to 46 of
50. The first evaluation predicate required the whole chunk in the answer;
it was corrected to check the quoted sentence against the stored passage.

## Deferred work

Credentialed semantic embedding and LLM evaluation, tokenizer-accurate
context limits, durable indexing with rate limits, retention, and adversarial
source-content tests remain open as CW-09 through CW-12. The local synthetic
baseline is not a claim about real semantic search quality.

## Exit decision

`IMPLEMENTED — EXIT GATE OPEN` until the final local and remote checks, clean
demo, security review, and release tag are complete. No v0.4 tag is claimed.
