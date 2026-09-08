# Milestone 1 Real-Provider Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a credential-safe, reproducible two-model provider baseline to the frozen Milestone 1 dataset while retaining the deterministic fake-provider baseline.

**Architecture:** Keep the application layer provider-neutral. The experiment script is the composition boundary: it receives explicit registered model names, constructs existing `FakeLLMClient` and `LiteLLMClient` instances, injects them into a provider-neutral runner, and writes metadata-only results to a new file so `results.jsonl` remains the frozen fake baseline.

**Tech Stack:** Python 3.12, pytest, Pydantic, existing Contextwise LLM contracts, LiteLLM, uv.

## Global Constraints

- Never place provider keys, raw prompts, raw responses, or provider payloads in source control or result artifacts.
- Preserve `experiments/provider-baseline-001/results.jsonl` as the deterministic fake-provider baseline.
- Supply both comparison model names and all provider credentials through environment variables at runtime; commit no provider-specific defaults.
- Reuse `Settings`, `ModelRegistry`, `GenerationService`, `LLMClient`, and `LiteLLMClient`; add no dependency.
- This plan establishes provider-baseline plumbing only. It does not close Milestone 1's quality, TTFT, cost, paired constrained-output, remote-CI, or full-security-review gaps.

---

## File Structure

- Create: `experiments/provider-baseline-001/runner.py` — provider-neutral configuration validation, case execution, and metadata-only result serialization.
- Create: `tests/test_baseline_runner.py` — deterministic coverage of configuration, artifact separation, and result redaction.
- Modify: `experiments/provider-baseline-001/run.py` — thin CLI that chooses fake or real comparison mode and delegates to the runner.
- Modify: `experiments/provider-baseline-001/README.md` — credential-safe commands and result-artifact contract.
- Modify: `docs/milestones/01-llm-gateway-typed-generation.md` — record the comparison only after observed evidence exists; retain CI/security debt.
- Modify: `docs/milestones/retrospectives/01-llm-gateway.md` — replace the deferred comparison item with observed comparison details after execution.
- Modify: `docs/learning/01-llm-gateway.md` — record the comparison lesson and limitations after execution.
- Modify: `docs/RELEASE_NOTES/0.1.0.md` — state that a real-provider baseline exists only after its artifact is committed.

### Task 1: Add a provider-neutral baseline runner

**Files:**
- Create: `experiments/provider-baseline-001/runner.py`
- Test: `tests/test_baseline_runner.py`

**Interfaces:**
- Consumes: an injected `GenerationService`, a `ModelRegistry`, registered model names, and `prompts.jsonl` case dictionaries containing `id`, `prompt`, and optional `response_schema`.
- Produces: `BaselineRunConfig(mode: Literal["fake", "comparison"], model_names: tuple[str, ...], output_path: Path)` and `BaselineResult` dictionaries with only `id`, `requested_model`, `provider`, `model`, `response_schema`, `structured_valid`, `total_latency_ms`, token counts, `estimated_cost_usd`, `retry_count`, `fallback_used`, and a stable non-secret `status`.

- [ ] **Step 1: Write failing runner tests.**

```python
def test_comparison_requires_exactly_two_distinct_registered_models(tmp_path: Path) -> None:
    config = BaselineRunConfig.comparison(("one", "one"), tmp_path / "comparison.jsonl")
    with pytest.raises(ValueError, match="two distinct"):
        config.validate(ModelRegistry((ModelDefinition("one", "fake", "one", frozenset()),)))


def test_serialized_results_exclude_prompt_response_and_secret(tmp_path: Path) -> None:
    result = BaselineResult.from_generation(
        case_id="case-1", response_schema=None, output=output, elapsed_ms=1.0
    )
    line = result.to_json_line()
    assert "prompt" not in line
    assert "response" not in line
    assert "OPENROUTER_API_KEY" not in line
```

- [ ] **Step 2: Run the tests to verify failure.**

Run: `uv run pytest tests/test_baseline_runner.py -q`

Expected: FAIL because `experiments/provider-baseline-001/runner.py` does not exist.

- [ ] **Step 3: Implement the minimal runner.**

```python
@dataclass(frozen=True)
class BaselineRunConfig:
    mode: Literal["fake", "comparison"]
    model_names: tuple[str, ...]
    output_path: Path

    def validate(self, registry: ModelRegistry) -> None:
        if self.mode == "comparison" and len(set(self.model_names)) != 2:
            raise ValueError("comparison mode requires two distinct registered models")
        for model_name in self.model_names:
            registry.get(model_name)
```

Implement a `run_cases()` coroutine that runs every frozen case once for each selected model, measures total latency with `perf_counter`, maps output to `BaselineResult`, and writes newline-delimited JSON only after all rows are prepared. Catch each `LLMError` per model/case and emit an expected row with a stable, non-secret status code rather than aborting the run. The runner receives an already-built service; it must not import `LiteLLMClient` or any infrastructure module, and it must not log requests or responses.

- [ ] **Step 4: Run focused verification.**

Run: `uv run pytest tests/test_baseline_runner.py -q && uv run mypy experiments/provider-baseline-001/runner.py`

Expected: PASS with no mypy errors.

### Task 2: Make the experiment CLI select a separate real-provider artifact

**Files:**
- Modify: `experiments/provider-baseline-001/run.py`
- Test: `tests/test_baseline_runner.py`

**Interfaces:**
- Consumes: `M1_BASELINE_MODE= fake | comparison`, `M1_BASELINE_MODELS=registered-name-a,registered-name-b`, `LLM_MODELS_JSON`, and standard provider credentials such as `OPENROUTER_API_KEY`.
- Produces: fake mode writes `experiments/provider-baseline-001/results.generated.jsonl` without overwriting frozen `results.jsonl`; comparison mode writes only `experiments/provider-baseline-001/real-provider-results.jsonl`.

- [ ] **Step 1: Write a failing CLI configuration test.**

```python
def test_comparison_output_path_cannot_replace_fake_baseline(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="results.jsonl is reserved"):
        BaselineRunConfig.comparison(("model-a", "model-b"), tmp_path / "results.jsonl")
```

- [ ] **Step 2: Run the test to verify failure.**

Run: `uv run pytest tests/test_baseline_runner.py::test_comparison_output_path_cannot_replace_fake_baseline -q`

Expected: FAIL until output-path validation is implemented.

- [ ] **Step 3: Replace the hard-coded fake service setup in `run.py`.**

```python
mode = os.environ.get("M1_BASELINE_MODE", "fake")
model_names = tuple(
    name.strip() for name in os.environ.get("M1_BASELINE_MODELS", "").split(",") if name.strip()
)
config = BaselineRunConfig.from_environment(
    directory=Path(__file__).parent,
    mode=mode,
    model_names=model_names,
)
await run_cases(config=config, settings=Settings(_env_file=None), cases_path=directory / "prompts.jsonl")
```

`from_environment()` must use `("fake-default",)` and `results.jsonl` for fake mode, require exactly two distinct configured non-fake model names and use `real-provider-results.jsonl` for comparison mode, and reject every other mode value. It must not print environment values or accept an output-path override. The CLI retains the existing explicit `DATABASE_URL` override when creating `Settings`, then constructs and injects fake/LiteLLM clients at this composition boundary.

- [ ] **Step 4: Run local deterministic checks.**

Run: `uv run pytest tests/test_baseline_runner.py -q && uv run ruff check experiments/provider-baseline-001/run.py experiments/provider-baseline-001/runner.py && uv run mypy experiments/provider-baseline-001/runner.py`

Expected: PASS.

### Task 3: Document and execute the bounded evidence workflow

**Files:**
- Modify: `experiments/provider-baseline-001/README.md`
- Modify: `docs/milestones/01-llm-gateway-typed-generation.md`
- Modify: `docs/milestones/retrospectives/01-llm-gateway.md`
- Modify: `docs/learning/01-llm-gateway.md`
- Modify: `docs/RELEASE_NOTES/0.1.0.md`

**Interfaces:**
- Consumes: a successful local `real-provider-results.jsonl` generated from the unchanged 30-case `prompts.jsonl` dataset.
- Produces: reviewed evidence notes that state requested/returned model identifiers, run date, completion and schema-validity counts, total-latency and token aggregates, and remaining gate debt without including secrets or raw content.

- [ ] **Step 1: Document the runtime command without credentials.**

Add this form to the experiment README, with names deliberately supplied by the operator:

```bash
export OPENROUTER_API_KEY='set outside source control'
export LLM_MODELS_JSON='[{"name":"candidate-a","provider":"openrouter","model":"provider/model-a","capabilities":["text","structured"]},{"name":"candidate-b","provider":"openrouter","model":"provider/model-b","capabilities":["text","structured"]}]'
export M1_BASELINE_MODE=comparison
export M1_BASELINE_MODELS=candidate-a,candidate-b
uv run python experiments/provider-baseline-001/run.py
```

The README must state that the shell line is an example, keys must never be committed, and the result file contains metadata only.

- [ ] **Step 2: Run the deterministic baseline before external evidence.**

Run: `uv run python experiments/provider-baseline-001/run.py && git diff -- experiments/provider-baseline-001/results.jsonl`

Expected: The fake baseline completes into `results.generated.jsonl`. The committed `results.jsonl` remains unchanged; do not replace it solely because wall-clock latency differs.

- [ ] **Step 3: Run the comparison only with an explicitly supplied credential.**

Run: `M1_BASELINE_MODE=comparison M1_BASELINE_MODELS=candidate-a,candidate-b uv run python experiments/provider-baseline-001/run.py`

Expected: Exit 0 and create `experiments/provider-baseline-001/real-provider-results.jsonl` with 60 rows, two distinct non-fake `requested_model` values, no `prompt`, `response`, or key fields, and every structured case marked valid or recorded with a non-secret failure status.

- [ ] **Step 4: Produce a checked aggregate from metadata.**

Run: `uv run python -c 'import json; from pathlib import Path; rows=[json.loads(x) for x in Path("experiments/provider-baseline-001/real-provider-results.jsonl").read_text().splitlines()]; models={r["requested_model"] for r in rows}; assert len(rows) == 60 and len(models) == 2; assert all("prompt" not in r and "response" not in r for r in rows); print({m: sum(r["total_latency_ms"] for r in rows if r["requested_model"] == m) / sum(r["requested_model"] == m for r in rows) for m in models})'`

Expected: Exit 0; use this aggregate plus structured-valid counts and token totals in the evidence notes. Leave cost comparisons unchecked because the existing generation service returns `None` for real-provider estimates.

- [ ] **Step 5: Update milestone evidence only from observed output.**

Record only the observed baseline execution. Preserve unchecked criteria for quality comparison, TTFT, cost, paired schema-constrained-versus-free-form comparison, remote CI, and the full security review. Update the retrospective, learning note, and release note with observed aggregates and limitations; do not assert `PASS` for the Milestone 1 exit gate.

- [ ] **Step 6: Run final local quality checks.**

Run: `make check && make test && make test-integration`

Expected: all commands exit 0. If provider calls fail due to quotas, credentials, or provider availability, leave the comparison criterion unchecked, keep any non-secret failure evidence separate from the fake baseline, and do not modify implementation code merely to make the gate appear closed.

## Plan Self-Review

- **Coverage:** The plan establishes a safe two-model provider-baseline capability, preserves frozen fake evidence, and records all measurement and exit-gate dependencies that remain.
- **Boundaries:** It does not expand into Milestone 2, quality scoring, paired schema comparison, provider-specific cost reconciliation, streaming time-to-first-token instrumentation, remote CI configuration, or a full security audit.
- **Consistency:** The frozen fake baseline remains `results.jsonl`; generated fake output is `results.generated.jsonl`; comparison evidence is always `real-provider-results.jsonl`; requested model identities are runtime-supplied registered names and returned provider aliases are recorded separately.
- **No placeholders:** All files, commands, expected outcomes, artifact names, and credential-handling rules are explicit.
