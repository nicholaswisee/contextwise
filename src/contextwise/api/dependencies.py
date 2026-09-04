import asyncio

from contextwise.application.llm.fake_client import FakeLLMClient
from contextwise.application.llm.generation_service import GenerationService
from contextwise.application.llm.model_registry import ModelRegistry
from contextwise.application.llm.prompt_registry import PromptRegistry
from contextwise.application.llm.schema_registry import SchemaRegistry
from contextwise.config import Settings
from contextwise.infrastructure.database import Database
from contextwise.infrastructure.invocations import InvocationRepository
from contextwise.infrastructure.llm.litellm_client import LiteLLMClient


class AppState:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.database = Database(settings)
        self.model_registry = ModelRegistry.from_settings(settings)
        self.prompt_registry = PromptRegistry()
        self.schema_registry = SchemaRegistry()
        self.invocation_repository = InvocationRepository(self.database.session_factory)
        self.llm_clients = {
            model.name: (
                FakeLLMClient()
                if model.provider == "fake"
                else LiteLLMClient(model.provider, settings.llm_timeout_seconds)
            )
            for model in self.model_registry.list()
        }
        self.generation_service = GenerationService(
            model_registry=self.model_registry,
            prompt_registry=self.prompt_registry,
            schema_registry=self.schema_registry,
            clients=self.llm_clients,
            repository=self.invocation_repository,
            max_retries=settings.llm_max_retries,
            structured_repair_attempts=settings.llm_structured_repair_attempts,
            fallback_model=settings.llm_fallback_model,
            primary_model=settings.llm_primary_model,
        )
        self.active_requests = 0
        self.requests_complete = asyncio.Event()
        self.requests_complete.set()

    def request_started(self) -> None:
        self.active_requests += 1
        self.requests_complete.clear()

    def request_finished(self) -> None:
        self.active_requests -= 1
        if self.active_requests == 0:
            self.requests_complete.set()

    async def wait_for_requests(self) -> None:
        await self.requests_complete.wait()


_state: AppState | None = None


def init_state(settings: Settings) -> AppState:
    global _state
    _state = AppState(settings)
    return _state


def get_state() -> AppState:
    global _state
    if _state is None:
        _settings = Settings()
        _state = AppState(_settings)
    return _state


def get_settings() -> Settings:
    return get_state().settings


def get_database() -> Database:
    return get_state().database


def get_generation_service() -> GenerationService:
    return get_state().generation_service


def get_invocation_repository() -> InvocationRepository:
    return get_state().invocation_repository
