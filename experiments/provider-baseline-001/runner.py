import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Literal, Protocol

from contextwise.application.llm.errors import LLMError
from contextwise.application.llm.generation_service import GenerationInput, GenerationOutput
from contextwise.application.llm.model_registry import ModelRegistry

BaselineMode = Literal["fake", "comparison"]


class GenerationServiceLike(Protocol):
    async def generate(self, input: GenerationInput, request_id: str) -> GenerationOutput: ...


@dataclass(frozen=True)
class BaselineRunConfig:
    mode: BaselineMode
    model_names: tuple[str, ...]
    output_path: Path

    @classmethod
    def fake(cls, directory: Path) -> "BaselineRunConfig":
        return cls("fake", ("fake-default",), directory / "results.generated.jsonl")

    @classmethod
    def comparison(cls, model_names: tuple[str, ...], output_path: Path) -> "BaselineRunConfig":
        if output_path.name == "results.jsonl":
            raise ValueError("results.jsonl is reserved for the fake baseline")
        return cls("comparison", model_names, output_path)

    @classmethod
    def from_environment(
        cls, directory: Path, mode: str, model_names: tuple[str, ...]
    ) -> "BaselineRunConfig":
        if mode == "fake":
            return cls.fake(directory)
        if mode == "comparison":
            if len(model_names) != 2:
                raise ValueError("comparison mode requires exactly two model names")
            return cls.comparison(model_names, directory / "real-provider-results.jsonl")
        raise ValueError("M1_BASELINE_MODE must be fake or comparison")

    def validate(self, registry: ModelRegistry) -> None:
        if self.mode == "comparison" and len(set(self.model_names)) != 2:
            raise ValueError("comparison mode requires two distinct model names")
        for model_name in self.model_names:
            definition = registry.get(model_name)
            if self.mode == "comparison" and definition.provider == "fake":
                raise ValueError("comparison mode cannot include fake providers")


@dataclass(frozen=True)
class BaselineResult:
    id: str
    requested_model: str
    provider: str | None
    model: str | None
    response_schema: str | None
    structured_valid: bool | None
    total_latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float | None
    retry_count: int
    fallback_used: bool
    status: str

    @classmethod
    def from_generation(
        cls,
        case_id: str,
        requested_model: str,
        response_schema: str | None,
        output: GenerationOutput,
        elapsed_ms: float,
    ) -> "BaselineResult":
        return cls(
            id=case_id,
            requested_model=requested_model,
            provider=output.provider,
            model=output.model,
            response_schema=response_schema,
            structured_valid=output.structured is not None if response_schema else None,
            total_latency_ms=round(elapsed_ms, 3),
            input_tokens=output.usage.input_tokens,
            output_tokens=output.usage.output_tokens,
            total_tokens=output.usage.total_tokens,
            estimated_cost_usd=output.estimated_cost_usd,
            retry_count=output.retry_count,
            fallback_used=output.fallback_used,
            status="completed",
        )

    @classmethod
    def from_error(
        cls,
        case_id: str,
        requested_model: str,
        response_schema: str | None,
        error: LLMError,
        elapsed_ms: float,
    ) -> "BaselineResult":
        return cls(
            id=case_id,
            requested_model=requested_model,
            provider=None,
            model=None,
            response_schema=response_schema,
            structured_valid=False if response_schema else None,
            total_latency_ms=round(elapsed_ms, 3),
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            estimated_cost_usd=None,
            retry_count=error.retry_count,
            fallback_used=False,
            status=error.code,
        )

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


async def run_cases(
    config: BaselineRunConfig,
    registry: ModelRegistry,
    service: GenerationServiceLike,
    cases: Sequence[Mapping[str, object]],
) -> None:
    config.validate(registry)
    results: list[str] = []
    for model_name in config.model_names:
        for case in cases:
            case_id = _required_string(case, "id")
            prompt = _required_string(case, "prompt")
            response_schema = _optional_string(case, "response_schema")
            started = perf_counter()
            try:
                output = await service.generate(
                    GenerationInput(
                        prompt=prompt,
                        model=model_name,
                        response_schema=response_schema,
                    ),
                    request_id=f"baseline-{case_id}-{model_name}",
                )
            except LLMError as error:
                result = BaselineResult.from_error(
                    case_id, model_name, response_schema, error, (perf_counter() - started) * 1000
                )
            else:
                result = BaselineResult.from_generation(
                    case_id, model_name, response_schema, output, (perf_counter() - started) * 1000
                )
            results.append(result.to_json_line())
    config.output_path.write_text("\n".join(results) + ("\n" if results else ""))


def _required_string(case: Mapping[str, object], key: str) -> str:
    value = case.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"baseline case requires non-empty {key}")
    return value


def _optional_string(case: Mapping[str, object], key: str) -> str | None:
    value = case.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"baseline case {key} must be a string")
    return value
