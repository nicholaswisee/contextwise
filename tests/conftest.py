import os
import subprocess

import pytest


@pytest.fixture(autouse=True)
def use_deterministic_fake_llm(monkeypatch):
    monkeypatch.setenv("LLM_PRIMARY_MODEL", "fake-default")
    monkeypatch.setenv("LLM_MODELS_JSON", "[]")
    monkeypatch.setenv("LLM_FALLBACK_MODEL", "")


def get_test_database_url():
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://contextwise:contextwise@localhost:5434/contextwise_test",
    )


@pytest.fixture(scope="session")
def apply_migrations():
    url = get_test_database_url()
    os.environ["DATABASE_URL"] = url
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], check=True)
    yield
    subprocess.run(["uv", "run", "alembic", "downgrade", "base"], check=True)
