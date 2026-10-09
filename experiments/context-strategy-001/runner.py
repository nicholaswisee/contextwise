import json
from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from contextwise.application.assistant.context_builder import ContextBuilder
from contextwise.application.assistant.contracts import ConversationMessage, TextPart

Strategy = Literal["full_transcript", "sliding_window", "frozen_summary"]
Category = Literal["pronoun", "correction", "conflicting_instruction"]


class CaseTurn(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1)


class StrategyCase(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: str = Field(alias="id", min_length=1)
    category: Category
    turns: tuple[CaseTurn, ...] = Field(min_length=2)
    expected_facts: tuple[str, ...] = Field(min_length=1)
    summary: str = Field(min_length=1)


class EvaluationResult(BaseModel):
    case_id: str
    strategy: Strategy
    rubric_passed: bool
    estimated_input_tokens: int
    output_tokens: int | None
    latency_ms: float
    truncated: bool
    overflowed: bool = False
    failure_code: str | None


def load_cases(path: Path) -> tuple[StrategyCase, ...]:
    return tuple(
        StrategyCase.model_validate(json.loads(line))
        for line in path.read_text().splitlines()
        if line.strip()
    )


def evaluate_case(
    case: StrategyCase,
    strategy: Strategy,
    token_budget: int = 4096,
    output_reserve: int = 512,
) -> EvaluationResult:
    started = perf_counter()
    try:
        ancestry = _messages_for(case, strategy)
        context = ContextBuilder().build(
            "You are Contextwise, a concise and helpful assistant.",
            ancestry,
            token_budget,
            output_reserve,
        )
        rendered = "\n".join(message.content.lower() for message in context.messages)
        passed = all(fact.lower() in rendered for fact in case.expected_facts)
        return EvaluationResult(
            case_id=case.case_id,
            strategy=strategy,
            rubric_passed=passed,
            estimated_input_tokens=context.estimated_input_tokens,
            output_tokens=None,
            latency_ms=round((perf_counter() - started) * 1000, 3),
            truncated=context.truncated,
            failure_code=None,
        )
    except Exception as error:
        return EvaluationResult(
            case_id=case.case_id,
            strategy=strategy,
            rubric_passed=False,
            estimated_input_tokens=0,
            output_tokens=None,
            latency_ms=round((perf_counter() - started) * 1000, 3),
            truncated=False,
            overflowed=True,
            failure_code=getattr(error, "code", "evaluation_error"),
        )


def run_cases(
    cases: tuple[StrategyCase, ...],
    output_path: Path,
    token_budget: int = 4096,
    output_reserve: int = 512,
) -> None:
    rows = [
        evaluate_case(case, strategy, token_budget, output_reserve).model_dump()
        for case in cases
        for strategy in ("full_transcript", "sliding_window", "frozen_summary")
    ]
    output_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n")


def _messages_for(case: StrategyCase, strategy: Strategy) -> tuple[ConversationMessage, ...]:
    if strategy == "full_transcript":
        selected = tuple(enumerate(case.turns))
    elif strategy == "sliding_window":
        selected = tuple(enumerate(case.turns[-4:], start=len(case.turns) - 4))
    else:
        selected = ((-1, CaseTurn(role="user", text=case.summary)),)
    return tuple(
        ConversationMessage(
            id=f"{case.case_id}-{index}",
            conversation_id=case.case_id,
            parent_id=None,
            role=turn.role,
            parts=(TextPart(text=turn.text),),
            status="completed",
        )
        for index, turn in selected
    )


if __name__ == "__main__":
    directory = Path(__file__).parent
    run_cases(load_cases(directory / "cases.jsonl"), directory / "results.generated.jsonl")
