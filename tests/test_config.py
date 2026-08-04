import pytest
from pydantic import ValidationError

from contextwise.config import Settings


def test_settings_require_database_url():
    with pytest.raises(ValidationError):
        Settings()


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    settings = Settings()
    assert str(settings.database_url) == "postgresql+asyncpg://user:pass@localhost/db"
    assert settings.log_level == "INFO"


def test_settings_reject_malformed_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "not-a-url")
    with pytest.raises(ValidationError):
        Settings()
