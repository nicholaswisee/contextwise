# Provider Baseline 001

This frozen dataset has 30 prompts: 20 free-form prompts and 10 requests using the registered `answer` schema. Run the deterministic fake-provider baseline with:

```bash
uv run python experiments/provider-baseline-001/run.py
```

The checked-in `results.jsonl` is the frozen deterministic fake-provider plumbing baseline. Running the command writes a fresh `results.generated.jsonl` artifact instead of overwriting the checked-in file. It records total latency, token accounting, structured-output validity, retry count, fallback use, and completion status. It does not claim real-model quality, time to first token, or provider cost.

To run two explicitly registered OpenRouter models, provide credentials and model configuration outside source control:

```bash
export OPENROUTER_API_KEY='set outside source control'
export LLM_MODELS_JSON='[{"name":"candidate-a","provider":"openrouter","model":"openrouter/provider/model-a","capabilities":["text","structured"]},{"name":"candidate-b","provider":"openrouter","model":"openrouter/provider/model-b","capabilities":["text","structured"]}]'
export M1_BASELINE_MODE=comparison
export M1_BASELINE_MODELS=candidate-a,candidate-b
uv run python experiments/provider-baseline-001/run.py
```

LiteLLM reads `OPENROUTER_API_KEY` from the environment. The model values must use LiteLLM's OpenRouter form, and the registered names in `M1_BASELINE_MODELS` must match the names in `LLM_MODELS_JSON`. Comparison output is written to `real-provider-results.jsonl`, never to the fake baseline file. Results contain metadata only: no prompts, responses, provider payloads, or credentials.

This repository does not contain a real-provider result because no credentialed run has been performed here. Cost comparison remains unavailable until provider-specific pricing is added, and the current artifact does not measure time to first token or paired free-form versus constrained-output quality.
