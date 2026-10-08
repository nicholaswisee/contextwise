import importlib.util
import json
from pathlib import Path

CASE_PATH = Path("experiments/context-strategy-001/cases.jsonl")
RUNNER_PATH = Path("experiments/context-strategy-001/runner.py")
SPEC = importlib.util.spec_from_file_location("context_strategy_runner", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

EvaluationResult = runner.EvaluationResult
load_cases = runner.load_cases


def test_cases_cover_required_multi_turn_categories() -> None:
    cases = load_cases(CASE_PATH)

    assert len(cases) == 20
    assert {case.category for case in cases} == {
        "pronoun",
        "correction",
        "conflicting_instruction",
    }


def test_result_rows_contain_metrics_without_raw_content() -> None:
    row = EvaluationResult(
        case_id="pronoun-01",
        strategy="sliding_window",
        rubric_passed=True,
        estimated_input_tokens=42,
        output_tokens=7,
        latency_ms=12,
        truncated=False,
        failure_code=None,
    ).model_dump()

    assert {"prompt", "response", "api_key"}.isdisjoint(row)


def test_stored_results_have_one_row_per_case_and_strategy() -> None:
    rows = [
        json.loads(line)
        for line in Path("experiments/context-strategy-001/results.jsonl").read_text().splitlines()
    ]

    assert len(rows) == 60
    assert {row["strategy"] for row in rows} == {
        "full_transcript",
        "sliding_window",
        "frozen_summary",
    }
