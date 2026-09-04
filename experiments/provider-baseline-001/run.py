import asyncio
import json
from pathlib import Path
from time import perf_counter

from contextwise.application.llm.fake_client import FakeLLMClient
from contextwise.application.llm.generation_service import GenerationInput, GenerationService
from contextwise.application.llm.model_registry import ModelRegistry
from contextwise.application.llm.prompt_registry import PromptRegistry
from contextwise.application.llm.schema_registry import SchemaRegistry
from contextwise.config import Settings


class MemoryInvocationRepository:
    def __init__(self) -> None:
        self.count = 0

    async def create_started(self, **kwargs: object) -> str:
        self.count += 1
        return f"evaluation-{self.count}"

    async def complete(self, *args: object, **kwargs: object) -> None:
        return None

    async def fail(self, *args: object, **kwargs: object) -> None:
        return None

    async def cancel(self, *args: object, **kwargs: object) -> None:
        return None


async def run() -> None:
    directory = Path(__file__).parent
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://contextwise:contextwise@localhost/contextwise",
    )
    registry = ModelRegistry.from_settings(settings)
    service = GenerationService(
        model_registry=registry,
        prompt_registry=PromptRegistry(),
        schema_registry=SchemaRegistry(),
        clients={"fake-default": FakeLLMClient()},
        repository=MemoryInvocationRepository(),
        max_retries=0,
        structured_repair_attempts=0,
        fallback_model=None,
        primary_model="fake-default",
    )
    results = []
    for line in (directory / "prompts.jsonl").read_text().splitlines():
        case = json.loads(line)
        started = perf_counter()
        output = await service.generate(
            GenerationInput(
                prompt=case["prompt"], response_schema=case.get("response_schema")
            ),
            request_id=case["id"],
        )
        results.append(
            {
                "id": case["id"],
                "provider": output.provider,
                "model": output.model,
                "response_schema": case.get("response_schema"),
                "structured_valid": output.structured is not None if case.get("response_schema") else None,
                "total_latency_ms": round((perf_counter() - started) * 1000, 3),
                "input_tokens": output.usage.input_tokens,
                "output_tokens": output.usage.output_tokens,
                "total_tokens": output.usage.total_tokens,
                "estimated_cost_usd": 0,
                "retry_count": output.retry_count,
                "fallback_used": output.fallback_used,
                "status": "completed",
            }
        )
    (directory / "results.jsonl").write_text(
        "".join(f"{json.dumps(result)}\n" for result in results)
    )


if __name__ == "__main__":
    asyncio.run(run())
