# Context Strategy 001 Evaluation

**Run:** 2026-09-10, local Python 3.12, deterministic application-layer run
**Dataset:** `experiments/context-strategy-001/cases.jsonl`
**Artifact:** `experiments/context-strategy-001/results.jsonl`

## Scope

The evaluation contains 20 manually authored multi-turn cases: 7 pronoun
cases, 7 correction cases, and 6 conflicting-instruction cases. It compares
the complete transcript, newest-four-turn sliding window, and manually authored
case summary. The runner exercises the application context builder directly,
not HTTP and not a credentialed model.

## Stored measurements

The artifact contains 60 rows, one per case and strategy. Each row records the
rubric result, estimated input tokens, local runner latency, output-token
availability, truncation/overflow flags, and a stable failure code. This run
has no provider output, so `output_tokens` is `null`.

| Strategy | Cases | Rubric passes | Input-token range | Truncated |
|---|---:|---:|---:|---:|
| `full_transcript` | 20 | 20 | 33–45 | 0 |
| `sliding_window` | 20 | 20 | 33–45 | 0 |
| `frozen_summary` | 20 | 20 | 24–36 | 0 |

The checked-in latency values are local plumbing measurements, not a
production performance claim. The rubric checks expected case facts against
the selected context; it does not measure the quality of a language model.

## Interpretation

For these short cases, all strategies retain the expected facts. The summary
strategy uses fewer estimated input tokens because the summaries were manually
written for each case. This is not evidence that automated summaries are safe
or better; longer-context overflow, summary drift, and generation quality need
their own later evaluation.

## Safety and reproducibility

The artifact contains no `prompt`, `response`, `api_key`, provider payload, or
credential field. Re-run the local generator with:

```bash
uv run python experiments/context-strategy-001/runner.py
```

That command writes `results.generated.jsonl` and leaves the frozen checked-in
artifact untouched.
