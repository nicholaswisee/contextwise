import asyncio
import json
import os
from pathlib import Path

from runner import BaselineRunConfig, run_cases

from contextwise.application.llm.contracts import LLMResult
from contextwise.application.llm.errors import LLMError
from contextwise.application.llm.fake_client import FakeLLMClient
from contextwise.application.llm.generation_service import GenerationService
from contextwise.application.llm.model_registry import ModelRegistry
from contextwise.application.llm.prompt_registry import PromptRegistry
from contextwise.application.llm.schema_registry import SchemaRegistry
from contextwise.config import Settings
from contextwise.infrastructure.llm.litellm_client import LiteLLMClient


class MemoryInvocationRepository:
    def __init__(self) -> None:
        self.count = 0

    async def create_started(
        self,
        request_id: str,
        provider: str,
        model: str,
        prompt_name: str | None,
        prompt_version: int | None,
    ) -> str:
        self.count += 1
        return f"evaluation-{self.count}"

    async def complete(
        self,
        invocation_id: str,
        result: LLMResult,
        latency_ms: int,
        retry_count: int,
        fallback_used: bool,
        estimated_cost_usd: float | None,
    ) -> None:
        return None

    async def fail(
        self,
        invocation_id: str,
        error: LLMError,
        latency_ms: int,
        retry_count: int,
        fallback_used: bool,
    ) -> None:
        return None

    async def cancel(self, invocation_id: str, latency_ms: int) -> None:
        return None


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://contextwise:contextwise@localhost/contextwise",
    )


def _cases(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


async def run() -> None:
    directory = Path(__file__).parent
    settings = _settings()
    registry = ModelRegistry.from_settings(settings)
    mode = os.environ.get("M1_BASELINE_MODE", "fake")
    model_names = tuple(
        name.strip() for name in os.environ.get("M1_BASELINE_MODELS", "").split(",") if name.strip()
    )
    config = BaselineRunConfig.from_environment(directory, mode, model_names)
    config.validate(registry)

    clients = {}
    for model in registry.list():
        clients[model.name] = (
            FakeLLMClient()
            if model.provider == "fake"
            else LiteLLMClient(model.provider, settings.llm_timeout_seconds)
        )
    service = GenerationService(
        model_registry=registry,
        prompt_registry=PromptRegistry(),
        schema_registry=SchemaRegistry(),
        clients=clients,
        repository=MemoryInvocationRepository(),
        max_retries=settings.llm_max_retries,
        structured_repair_attempts=settings.llm_structured_repair_attempts,
        fallback_model=None,
        primary_model=config.model_names[0],
    )
    await run_cases(config, registry, service, _cases(directory / "prompts.jsonl"))


if __name__ == "__main__":
    asyncio.run(run())
