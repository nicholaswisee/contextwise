import os
import subprocess

import pytest


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
