# Provider Baseline 001

This frozen dataset has 30 prompts: 20 free-form prompts and 10 requests using the registered `answer` schema. Run it with:

```bash
uv run python experiments/provider-baseline-001/run.py
```

The checked-in result is a deterministic fake-provider plumbing baseline. It records total latency, token accounting, structured-output validity, retry count, fallback use, and completion status. It does not claim real-model quality, time to first token, or provider cost.

No real provider comparison was run because this environment has no configured provider credentials. When a provider key is explicitly supplied, add a separate result file rather than overwriting the fake baseline.
