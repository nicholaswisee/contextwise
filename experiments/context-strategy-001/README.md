# Context Strategy 001

This frozen evaluation contains 20 manually authored multi-turn cases across
pronoun resolution, corrections, and conflicting instructions. The runner
compares three application-layer context strategies without going through HTTP:

- `full_transcript` retains the complete case transcript;
- `sliding_window` retains the newest four turns;
- `frozen_summary` uses the case-local manually authored summary.

Run the fake, deterministic evaluation with:

```bash
uv run python experiments/context-strategy-001/runner.py
```

The command writes `results.generated.jsonl`. The checked-in `results.jsonl`
contains metadata only: case ID, strategy, rubric result, estimated input
tokens, latency, truncation/overflow flags, and a stable failure code. It does
not contain prompts, responses, credentials, or provider payloads. No
credentialed model-quality result is claimed by this artifact.
