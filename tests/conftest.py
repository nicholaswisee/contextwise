import os
import subprocess

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


def get_test_database_url():
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://contextwise:contextwise@localhost:5434/contextwise_test",
    )


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    url = get_test_database_url()
    os.environ["DATABASE_URL"] = url
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], check=True)
    yield
    # Optionally downgrade after session
    subprocess.run(["uv", "run", "alembic", "downgrade", "base"], check=True)


@pytest.fixture
async def db_session():
    from contextwise.api.dependencies import get_state

    state = get_state()
    async with state.database.session_factory() as session:
        yield session
