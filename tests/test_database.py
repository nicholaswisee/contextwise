import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from contextwise.config import Settings
from contextwise.infrastructure.database import Database


@pytest.fixture
def settings(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    return Settings()


def test_database_creates_async_engine(settings):
    db = Database(settings)
    assert db.engine is not None


def test_get_session_yields_async_session(settings):
    db = Database(settings)
    session = db.session_factory()
    assert isinstance(session, AsyncSession)


def test_database_str_url(settings):
    db = Database(settings)
    assert "postgresql+asyncpg" in str(db.engine.url)
