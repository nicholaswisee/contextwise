from contextwise.config import Settings
from contextwise.infrastructure.database import Database


class AppState:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.database = Database(settings)


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
