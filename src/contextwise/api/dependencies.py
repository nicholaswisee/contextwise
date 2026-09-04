import asyncio

from contextwise.config import Settings
from contextwise.infrastructure.database import Database


class AppState:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.database = Database(settings)
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
