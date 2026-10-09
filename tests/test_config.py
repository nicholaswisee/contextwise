import pytest
from pydantic import ValidationError

from contextwise.config import Settings


def test_settings_require_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    settings = Settings()
    assert str(settings.database_url) == "postgresql+asyncpg://user:pass@localhost/db"
    assert settings.log_level == "INFO"


def test_settings_reject_malformed_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "not-a-url")
    with pytest.raises(ValidationError):
        Settings()


def test_production_rejects_default_owner_token(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("CONTEXTWISE_OWNER_TOKEN", raising=False)
    with pytest.raises(ValidationError, match="non-default CONTEXTWISE_OWNER_TOKEN"):
        Settings(_env_file=None)
