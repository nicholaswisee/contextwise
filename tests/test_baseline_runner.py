import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from contextwise.application.llm.errors import LLMProviderError
from contextwise.application.llm.model_registry import ModelDefinition, ModelRegistry

RUNNER_PATH = Path(__file__).parents[1] / "experiments/provider-baseline-001/runner.py"
SPEC = importlib.util.spec_from_file_location("baseline_runner", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
baseline_runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline_runner)

BaselineResult = baseline_runner.BaselineResult
BaselineRunConfig = baseline_runner.BaselineRunConfig
run_cases = baseline_runner.run_cases


def registry() -> ModelRegistry:
    return ModelRegistry(
        (
            ModelDefinition("fake-default", "fake", "fake-default", frozenset({"text"})),
            ModelDefinition(
                "candidate-a", "openrouter", "openrouter/provider/a", frozenset({"text"})
            ),
            ModelDefinition(
                "candidate-b", "openrouter", "openrouter/provider/b", frozenset({"text"})
            ),
        )
    )


def test_comparison_requires_two_distinct_non_fake_registered_models(tmp_path: Path) -> None:
    config = BaselineRunConfig.comparison(
        ("candidate-a", "candidate-a"), tmp_path / "comparison.jsonl"
    )

    with pytest.raises(ValueError, match="two distinct"):
        config.validate(registry())

    fake_config = BaselineRunConfig.comparison(
        ("fake-default", "candidate-a"), tmp_path / "comparison.jsonl"
    )
    with pytest.raises(ValueError, match="fake providers"):
        fake_config.validate(registry())

    aliased_fake_registry = ModelRegistry(
        (
            ModelDefinition("fake-alias", "fake", "fake-default", frozenset({"text"})),
            ModelDefinition(
                "candidate-a", "openrouter", "openrouter/provider/a", frozenset({"text"})
            ),
        )
    )
    aliased_fake_config = BaselineRunConfig.comparison(
        ("fake-alias", "candidate-a"), tmp_path / "comparison.jsonl"
    )
    with pytest.raises(ValueError, match="fake providers"):
        aliased_fake_config.validate(aliased_fake_registry)


def test_fake_runs_use_a_generated_artifact_path(tmp_path: Path) -> None:
    assert BaselineRunConfig.fake(tmp_path).output_path.name == "results.generated.jsonl"


def test_comparison_output_path_cannot_replace_fake_baseline(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="results.jsonl is reserved"):
        BaselineRunConfig.comparison(("candidate-a", "candidate-b"), tmp_path / "results.jsonl")


def test_serialized_result_excludes_prompt_response_and_secret() -> None:
    output = SimpleNamespace(
        provider="openrouter",
        model="provider/a",
        structured=None,
        usage=SimpleNamespace(input_tokens=2, output_tokens=3, total_tokens=5),
        estimated_cost_usd=None,
        latency_ms=12,
        retry_count=0,
        fallback_used=False,
    )
    result = BaselineResult.from_generation(
        case_id="case-1",
        requested_model="candidate-a",
        response_schema=None,
        output=output,
        elapsed_ms=12.5,
    )

    serialized = result.to_json_line()
    payload = json.loads(serialized)
    assert payload["requested_model"] == "candidate-a"
    assert "prompt" not in payload
    assert "text" not in payload
    assert "OPENROUTER_API_KEY" not in serialized


@pytest.mark.asyncio
async def test_run_cases_keeps_failed_model_cases_and_writes_metadata_only(tmp_path: Path) -> None:
    class Service:
        async def generate(self, input, request_id):
            if input.model == "candidate-b":
                raise LLMProviderError("secret provider payload")
            return SimpleNamespace(
                provider="openrouter",
                model="provider/a-returned",
                structured=None,
                usage=SimpleNamespace(input_tokens=1, output_tokens=2, total_tokens=3),
                estimated_cost_usd=None,
                latency_ms=4,
                retry_count=0,
                fallback_used=False,
            )

    output_path = tmp_path / "real-provider-results.jsonl"
    config = BaselineRunConfig.comparison(("candidate-a", "candidate-b"), output_path)
    cases = [{"id": "case-1", "prompt": "private prompt"}]

    await run_cases(config, registry(), Service(), cases)

    rows = [json.loads(line) for line in output_path.read_text().splitlines()]
    assert len(rows) == 2
    assert {row["requested_model"] for row in rows} == {"candidate-a", "candidate-b"}
    assert {row["status"] for row in rows} == {"completed", "provider_error"}
    assert all("private prompt" not in output_path.read_text() for _ in [0])
    assert "secret provider payload" not in output_path.read_text()
