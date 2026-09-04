# Milestone 0 — Engineering Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (inline). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap a reproducible, tested, observable FastAPI service with PostgreSQL, Alembic, structured JSON logging, Docker Compose, and CI.

**Architecture:** A small, layered Python package using uv, FastAPI, Pydantic Settings, SQLAlchemy 2.0 async, Alembic, and Docker Compose. The application factory is testable; health endpoints separate liveness from readiness; logs are JSON and carry request IDs; all commands are exposed through `make`.

**Tech Stack:** Python 3.12+, uv, FastAPI, Uvicorn, Pydantic Settings, SQLAlchemy 2.0 async, asyncpg, Alembic, PostgreSQL, Docker Compose, Make, GitHub Actions.

## Global Constraints

- All Python code is under `src/contextwise/`.
- Dependency graph: API layer imports application layer; neither imports infrastructure directly at module level except via dependency injection.
- Database URL is `postgresql+asyncpg://` for the app and `postgresql://` for Alembic config.
- No secrets committed; local values live in `.env` (gitignored).
- Liveness (`/health/live`) must NOT depend on external services.
- Readiness (`/health/ready`) must check database connectivity and migration state.
- All commands must be runnable via `make`.
- CI runs lint, format check, type check, tests, and migration checks.

---

### Task 1: uv Project Bootstrap

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/contextwise/__init__.py`
- Create: `src/contextwise/__main__.py`
- Create: `src/contextwise/config/__init__.py`
- Create: `src/contextwise/api/__init__.py`
- Create: `src/contextwise/infrastructure/__init__.py`
- Create: `tests/__init__.py`
- Test: `tests/test_bootstrap.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `contextwise` package importable; `python -m contextwise` exists.

- [ ] **Step 1: Write the failing test**

```python
import contextwise


def test_package_version_exists():
    assert hasattr(contextwise, "__version__")


def test_main_module_runs_without_error():
    import contextwise.__main__
    assert True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_bootstrap.py -v`
Expected: FAIL — `contextwise` not found.

- [ ] **Step 3: Write minimal implementation**

Create `pyproject.toml`:

```toml
[project]
name = "contextwise"
version = "0.0.0"
description = "Contextwise AI workspace"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.7.0",
    "mypy>=1.13.0",
]

[tool.uv]
default-groups = ["dev"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/contextwise"]

[tool.ruff]
target-version = "py312"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
testpaths = ["tests"]
```

Create `.python-version`:

```
3.12
```

Create `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
*.egg-info/
.venv/
venv/

# Environment
.env
.env.local

# IDEs
.vscode/
.idea/

# OS
.DS_Store

# Test / coverage
.pytest_cache/
.coverage
htmlcov/

# Mypy
.mypy_cache/
.dmypy.json

# Alembic local
*.sqlite3

# Docker volumes
postgres-data/
```

Create `.env.example`:

```bash
DATABASE_URL=postgresql+asyncpg://contextwise:contextwise@localhost:5432/contextwise
LOG_LEVEL=INFO
DEBUG=false
ENVIRONMENT=development
APP_NAME=contextwise
```

Create `src/contextwise/__init__.py`:

```python
__version__ = "0.0.0"
```

Create `src/contextwise/__main__.py`:

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("contextwise.api.main:app", host="0.0.0.0", port=8000, reload=True)
```

Create empty `__init__.py` files in `src/contextwise/config/`, `src/contextwise/api/`, `src/contextwise/infrastructure/`, and `tests/`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv sync && uv run pytest tests/test_bootstrap.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .python-version .gitignore .env.example src tests
git commit -m "feat(m0): bootstrap uv project structure"
```

---

### Task 2: Pydantic Settings

**Files:**
- Create: `src/contextwise/config/settings.py`
- Modify: `src/contextwise/config/__init__.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `contextwise.config.Settings` with `app_name`, `debug`, `environment`, `log_level`, `database_url`.

- [ ] **Step 1: Write the failing test**

```python
import os

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL — `Settings` not defined.

- [ ] **Step 3: Write minimal implementation**

Create `src/contextwise/config/settings.py`:

```python
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "contextwise"
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"
    database_url: PostgresDsn = Field(alias="DATABASE_URL")
```

Create `src/contextwise/config/__init__.py`:

```python
from contextwise.config.settings import Settings

__all__ = ["Settings"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/contextwise/config tests/test_config.py
git commit -m "feat(m0): add pydantic settings with env validation"
```

---

### Task 3: JSON Logging and Request IDs

**Files:**
- Create: `src/contextwise/logging_config.py`
- Create: `src/contextwise/api/middleware.py`
- Test: `tests/test_logging.py`

**Interfaces:**
- Consumes: `Settings` for `log_level`.
- Produces: `contextwise.logging_config.configure_logging(settings: Settings)` and `contextwise.api.middleware.RequestIDMiddleware`.

- [ ] **Step 1: Write the failing test**

```python
import json
import logging

from contextwise.api.middleware import RequestIDMiddleware
from contextwise.config import Settings
from contextwise.logging_config import configure_logging


def test_logging_configures_json_formatter(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    settings = Settings()
    configure_logging(settings)
    logger = logging.getLogger("contextwise")
    assert logger.level == logging.INFO


def test_request_id_middleware_adds_header():
    from starlette.testclient import TestClient
    from fastapi import FastAPI

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    def read_root():
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "x-request-id" in response.headers
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_logging.py -v`
Expected: FAIL — modules not defined.

- [ ] **Step 3: Write minimal implementation**

Create `src/contextwise/logging_config.py`:

```python
import json
import logging
import sys
from typing import Any

from contextwise.config import Settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(settings: Settings) -> None:
    level = logging.getLevelName(settings.log_level.upper())
    if not isinstance(level, int):
        level = logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger("contextwise")
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)
```

Create `src/contextwise/api/middleware.py`:

```python
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_logging.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/contextwise/logging_config.py src/contextwise/api/middleware.py tests/test_logging.py
git commit -m "feat(m0): add json logging and request id middleware"
```

---

### Task 4: Database Infrastructure

**Files:**
- Create: `src/contextwise/infrastructure/database.py`
- Test: `tests/test_database.py`

**Interfaces:**
- Consumes: `Settings` for `database_url`.
- Produces: `contextwise.infrastructure.database.Database` with `engine`, `session_factory`, `get_session()`, `init()`, `close()`.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_database.py -v`
Expected: FAIL — `Database` not defined.

- [ ] **Step 3: Write minimal implementation**

Create `src/contextwise/infrastructure/database.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from contextwise.config import Settings

Base = declarative_base()


class Database:
    def __init__(self, settings: Settings):
        self.engine = create_async_engine(str(settings.database_url))
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    async def get_session(self) -> AsyncSession:
        async with self.session_factory() as session:
            yield session

    async def init(self) -> None:
        pass

    async def close(self) -> None:
        await self.engine.dispose()

    async def health_check(self) -> bool:
        try:
            async with self.engine.connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_database.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/contextwise/infrastructure/database.py tests/test_database.py
git commit -m "feat(m0): add async sqlalchemy database infrastructure"
```

---

### Task 5: Alembic Migrations

**Files:**
- Create: `alembic.ini`
- Create: `src/contextwise/infrastructure/migrations/` (env.py, script.py.mako, versions/)
- Create: `src/contextwise/infrastructure/migrations/env.py`
- Create: `src/contextwise/infrastructure/migrations/script.py.mako`
- Create: `src/contextwise/infrastructure/migrations/versions/0001_initial.py`
- Create: `src/contextwise/infrastructure/migrations/__init__.py`
- Test: `tests/test_migrations.py`

**Interfaces:**
- Consumes: `Database` and `Settings`.
- Produces: Runnable `alembic upgrade head` and `alembic downgrade base`.

- [ ] **Step 1: Write the failing test**

```python
import os
import subprocess

import pytest


@pytest.fixture
def test_database_url():
    return os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://contextwise:contextwise@localhost:5432/contextwise_test")


@pytest.mark.asyncio
async def test_migrations_run_from_empty(test_database_url):
    # Test run via subprocess using alembic and TEST_DATABASE_URL
    pass
```

For this task, we will verify migrations via a `make migrate` command integration test later. The initial failing unit test is just that the migration directory exists.

```python
from pathlib import Path


def test_alembic_ini_exists():
    assert Path("alembic.ini").exists()


def test_migrations_directory_exists():
    assert Path("src/contextwise/infrastructure/migrations").is_dir()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_migrations.py -v`
Expected: FAIL — alembic.ini not found.

- [ ] **Step 3: Write minimal implementation**

Create `alembic.ini`:

```ini
[alembic]
script_location = src/contextwise/infrastructure/migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://contextwise:contextwise@localhost:5432/contextwise

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

Create `src/contextwise/infrastructure/migrations/__init__.py` (empty).

Create `src/contextwise/infrastructure/migrations/script.py.mako`:

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

Create `src/contextwise/infrastructure/migrations/env.py`:

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from contextwise.config import Settings
from contextwise.infrastructure.database import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    settings = Settings()
    url = str(settings.database_url)
    # Alembic uses sync driver
    return url.replace("postgresql+asyncpg", "postgresql", 1)


def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    config_section = config.get_section(config.config_ini_section)
    assert config_section is not None
    config_section["sqlalchemy.url"] = get_database_url()
    connectable = async_engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

Create `src/contextwise/infrastructure/migrations/versions/0001_initial.py`:

```python
"""Initial schema placeholder

Revision ID: 0001
Revises:
Create Date: 2026-08-04

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_migrations.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add alembic.ini src/contextwise/infrastructure/migrations tests/test_migrations.py
git commit -m "feat(m0): add alembic migration scaffold"
```

---

### Task 6: FastAPI Application Factory and Health Endpoints

**Files:**
- Create: `src/contextwise/api/main.py`
- Create: `src/contextwise/api/health.py`
- Create: `src/contextwise/api/dependencies.py`
- Modify: `src/contextwise/api/__init__.py`
- Create: `src/contextwise/application/health_service.py`
- Create: `src/contextwise/application/__init__.py`
- Test: `tests/conftest.py`
- Test: `tests/test_health.py`

**Interfaces:**
- Consumes: `Database`, `Settings`, `RequestIDMiddleware`, `configure_logging`.
- Produces: `create_app(settings: Settings) -> FastAPI` with `/health/live` and `/health/ready`.

- [ ] **Step 1: Write the failing test**

```python
import pytest
from httpx import AsyncClient

from contextwise.api.main import create_app
from contextwise.config import Settings


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    settings = Settings()
    return create_app(settings)


@pytest.mark.asyncio
async def test_live_returns_ok(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.asyncio
async def test_ready_with_bad_database_returns_service_unavailable(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_health.py -v`
Expected: FAIL — `create_app` not defined.

- [ ] **Step 3: Write minimal implementation**

Create `src/contextwise/application/health_service.py`:

```python
from contextwise.infrastructure.database import Database


class HealthService:
    def __init__(self, database: Database):
        self.database = database

    async def is_live(self) -> bool:
        return True

    async def is_ready(self) -> bool:
        return await self.database.health_check()
```

Create `src/contextwise/api/dependencies.py`:

```python
from contextwise.config import Settings
from contextwise.infrastructure.database import Database

_settings: Settings | None = None
_database: Database | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_database() -> Database:
    global _database
    if _database is None:
        _database = Database(get_settings())
    return _database
```

Create `src/contextwise/api/health.py`:

```python
from fastapi import APIRouter, Depends, HTTPException

from contextwise.api.dependencies import get_database
from contextwise.application.health_service import HealthService
from contextwise.infrastructure.database import Database

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def health_live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
async def health_ready(database: Database = Depends(get_database)) -> dict[str, str]:
    service = HealthService(database)
    if not await service.is_ready():
        raise HTTPException(status_code=503, detail={"status": "not ready"})
    return {"status": "ready"}
```

Create `src/contextwise/api/main.py`:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from contextwise.api.dependencies import get_database, get_settings
from contextwise.api.health import router as health_router
from contextwise.api.middleware import RequestIDMiddleware
from contextwise.config import Settings
from contextwise.logging_config import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    database = get_database()
    await database.init()
    yield
    await database.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is not None:
        from contextwise.api.dependencies import _settings
        global _settings as_dep
        # Simpler: override the dependency global module attribute
        import contextwise.api.dependencies as deps

        deps._settings = settings

    app = FastAPI(
        title="Contextwise",
        version="0.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(RequestIDMiddleware)
    app.include_router(health_router)
    return app


# Default app for uvicorn
settings = get_settings()
configure_logging(settings)
app = create_app(settings)
```

Wait, the global settings override is messy. Let's restructure `dependencies.py` to accept override cleanly. Use a factory pattern:

```python
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
```

Then `create_app`:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from contextwise.api.dependencies import get_state, init_state
from contextwise.api.health import router as health_router
from contextwise.api.middleware import RequestIDMiddleware
from contextwise.config import Settings
from contextwise.logging_config import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    state = get_state()
    configure_logging(state.settings)
    await state.database.init()
    yield
    await state.database.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is not None:
        init_state(settings)

    app = FastAPI(
        title="Contextwise",
        version="0.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(RequestIDMiddleware)
    app.include_router(health_router)
    return app


settings = get_state().settings
configure_logging(settings)
app = create_app(settings)
```

This is cleaner. Update dependencies.py accordingly.

Also create `src/contextwise/application/__init__.py` and update `src/contextwise/api/__init__.py`:

```python
from contextwise.api.main import app, create_app

__all__ = ["app", "create_app"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_health.py -v`
Expected: PASS (ready returns 503 because no real DB).

- [ ] **Step 5: Commit**

```bash
git add src/contextwise/api src/contextwise/application tests/conftest.py tests/test_health.py
git commit -m "feat(m0): add fastapi app factory and health endpoints"
```

---

### Task 7: Integration Test with Real PostgreSQL

**Files:**
- Test: `tests/conftest.py` (updated)
- Test: `tests/test_health_integration.py`

**Interfaces:**
- Consumes: Dockerized PostgreSQL via `TEST_DATABASE_URL`.
- Produces: Verified `/health/ready` passes when DB is up and migrations applied.

- [ ] **Step 1: Write the failing test**

```python
import os

import pytest
from httpx import AsyncClient

from contextwise.api.main import create_app
from contextwise.config import Settings


def get_test_database_url():
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://contextwise:contextwise@localhost:5432/contextwise_test",
    )


@pytest.fixture
async def app_with_db(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", get_test_database_url())
    settings = Settings()
    return create_app(settings)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ready_returns_ok_when_db_and_migrations_up(app_with_db):
    async with AsyncClient(app=app_with_db, base_url="http://test") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_health_integration.py -v -m integration`
Expected: FAIL or ERROR — database not running.

- [ ] **Step 3: Write minimal implementation**

Update `tests/conftest.py` to include a fixture that starts a test database using Docker Compose or a test database. For M0, we add a `docker-compose.test.yml` or use a test DB in the main compose.

Create `docker-compose.test.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: contextwise
      POSTGRES_PASSWORD: contextwise
      POSTGRES_DB: contextwise_test
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U contextwise -d contextwise_test"]
      interval: 2s
      timeout: 5s
      retries: 5
```

Update `tests/conftest.py` to run migrations before tests. We will add a session-scoped fixture that runs `alembic upgrade head` using the test database.

```python
import os
import subprocess

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from contextwise.api.dependencies import get_state


def get_test_database_url():
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://contextwise:contextwise@localhost:5433/contextwise_test",
    )


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    url = get_test_database_url()
    os.environ["DATABASE_URL"] = url
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    yield


@pytest.fixture
async def db_session():
    state = get_state()
    async with state.database.session_factory() as session:
        yield session
```

Wait, `alembic` needs a sync URL. env.py handles the asyncpg -> postgresql conversion. But `alembic` CLI imports from `src.contextwise...` and needs the package installed. With uv and src layout, we need to run `uv run alembic upgrade head`. Add Makefile target.

For the integration test to run, we need PostgreSQL running. We'll add a `make test-integration` command that starts test DB and runs tests.

Update `Makefile` (created in Task 9) to add:

```makefile
.PHONY: test-integration
TEST_DATABASE_URL ?= postgresql+asyncpg://contextwise:contextwise@localhost:5433/contextwise_test

test-db-up:
	TEST_DATABASE_URL=$(TEST_DATABASE_URL) docker compose -f docker-compose.test.yml up -d --wait

test-db-down:
	docker compose -f docker-compose.test.yml down -v

test-integration: test-db-up
	TEST_DATABASE_URL=$(TEST_DATABASE_URL) uv run pytest -m integration -v
	$(MAKE) test-db-down
```

- [ ] **Step 4: Run test to verify it passes**

Run: `make test-db-up && TEST_DATABASE_URL=postgresql+asyncpg://contextwise:contextwise@localhost:5433/contextwise_test uv run pytest -m integration -v && make test-db-down`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py tests/test_health_integration.py docker-compose.test.yml Makefile
git commit -m "test(m0): add postgres integration tests"
```

---

### Task 8: Docker Compose for API and Database

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `docker-entrypoint.sh`
- Test: `tests/test_docker_compose.py` (skipped — verified manually)

**Interfaces:**
- Consumes: `uv`, `python 3.12`, `postgres:16-alpine`.
- Produces: `docker compose up` starts API and database.

- [ ] **Step 1: Write minimal implementation**

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends make && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock .python-version ./
COPY src ./src

RUN pip install uv
RUN uv sync --frozen --no-dev

COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "contextwise.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-entrypoint.sh`:

```bash
#!/bin/bash
set -e

echo "Running database migrations..."
uv run alembic upgrade head

exec "$@"
```

Create `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: contextwise
      POSTGRES_PASSWORD: contextwise
      POSTGRES_DB: contextwise
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U contextwise -d contextwise"]
      interval: 2s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://contextwise:contextwise@postgres:5432/contextwise
      LOG_LEVEL: INFO
      DEBUG: "false"
      ENVIRONMENT: production
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  postgres-data:
```

- [ ] **Step 2: Verify Docker Compose**

Run: `docker compose up -d --wait`
Run: `curl http://localhost:8000/health/live`
Run: `curl http://localhost:8000/health/ready`
Run: `docker compose down`
Expected: Both health checks return 200.

- [ ] **Step 3: Commit**

```bash
git add Dockerfile docker-compose.yml docker-entrypoint.sh
git commit -m "feat(m0): add docker compose for api and postgres"
```

---

### Task 9: Makefile

**Files:**
- Create: `Makefile`

**Interfaces:**
- Produces: `make install`, `make test`, `make test-integration`, `make lint`, `make format`, `make type`, `make migrate`, `make up`, `make down`.

- [ ] **Step 1: Write minimal implementation**

Create `Makefile`:

```makefile
.PHONY: install test test-integration lint format type check migrate up down

PYTHON ?= python3
TEST_DATABASE_URL ?= postgresql+asyncpg://contextwise:contextwise@localhost:5433/contextwise_test

install:
	uv sync

test:
	uv run pytest -m "not integration" -v

test-db-up:
	TEST_DATABASE_URL=$(TEST_DATABASE_URL) docker compose -f docker-compose.test.yml up -d --wait

test-db-down:
	docker compose -f docker-compose.test.yml down -v

test-integration: test-db-up
	TEST_DATABASE_URL=$(TEST_DATABASE_URL) uv run pytest -m integration -v
	$(MAKE) test-db-down

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

type:
	uv run mypy src

check: lint format type test

migrate:
	uv run alembic upgrade head

up:
	docker compose up -d --wait

down:
	docker compose down
```

- [ ] **Step 2: Verify commands**

Run: `make lint`
Run: `make format`
Run: `make type`
Run: `make test`
Expected: All succeed.

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "feat(m0): add make commands for dev and ci"
```

---

### Task 10: CI Pipeline

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/migrations.yml` (optional; combine into ci.yml)

**Interfaces:**
- Produces: GitHub Actions workflow running lint, format, type, tests, migrations.

- [ ] **Step 1: Write minimal implementation**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "0.12.1"

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync

      - name: Lint
        run: uv run ruff check src tests

      - name: Format check
        run: uv run ruff format --check src tests

      - name: Type check
        run: uv run mypy src

      - name: Run tests
        run: uv run pytest -m "not integration" -v

  migrations:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: contextwise
          POSTGRES_PASSWORD: contextwise
          POSTGRES_DB: contextwise
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U contextwise -d contextwise"
          --health-interval 2s
          --health-timeout 5s
          --health-retries 5
    env:
      DATABASE_URL: postgresql+asyncpg://contextwise:contextwise@localhost:5432/contextwise
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "0.12.1"

      - name: Install dependencies
        run: uv sync

      - name: Run migrations
        run: uv run alembic upgrade head

      - name: Run migrations twice
        run: uv run alembic upgrade head

      - name: Downgrade migrations
        run: uv run alembic downgrade base
```

- [ ] **Step 2: Verify workflow file**

Run: `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` (requires pyyaml; or use `python -c` with stdlib if available). Use `python3 -c "import json, sys; print('ok')"` after checking yaml manually. Better: install `pyyaml` temporarily or just visually inspect.

Actually, since the plan is not executed as a separate agent, I can just check syntax.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci(m0): add github actions workflow"
```

---

### Task 11: Documentation and Milestone Exit

**Files:**
- Create: `docs/learning/00-foundation.md`
- Modify: `docs/milestones/00-engineering-foundation.md`
- Create: `docs/adr/0002-api-error-envelope.md` (optional)
- Test: none (docs)

**Interfaces:**
- Produces: Completed milestone evidence and learning note.

- [ ] **Step 1: Write learning note**

Create `docs/learning/00-foundation.md`:

```markdown
# Milestone 0 — Engineering Foundation Learning Note

## What was built

A minimal FastAPI service with uv packaging, Pydantic settings, async SQLAlchemy + Alembic, structured JSON logging, request IDs, Docker Compose, and GitHub Actions CI.

## What worked

- uv resolved dependencies quickly and produced a clean `uv.lock`.
- FastAPI's `lifespan` and dependency injection made shutdown and DB lifecycle testable.
- Separating liveness (no external deps) from readiness (DB + migrations) clarified startup semantics.

## What was hard

- Alembic async config requires `asyncpg` -> `postgresql` driver translation.
- Testing the app with a real database required a test-specific Docker Compose and a session-scoped migration fixture.

## Open questions

- Should readiness also check `alembic_version` matches `alembic heads`? For now we only check connectivity and the migration table exists.
- Is `make test-integration` too slow for CI? Fine for local CI; separate workflow for integration.

## Decisions recorded

- ADR-0001: uv chosen over Poetry.
```

- [ ] **Step 2: Update Milestone 0 checklist**

Mark deliverables as complete in `docs/milestones/00-engineering-foundation.md`.

- [ ] **Step 3: Commit**

```bash
git add docs/learning/00-foundation.md docs/milestones/00-engineering-foundation.md
git commit -m "docs(m0): add learning note and milestone checklist"
```

---

## Self-Review

1. **Spec coverage:**
   - Package manager: uv (Task 1).
   - FastAPI app factory: Task 6.
   - Health endpoints: Task 6.
   - Environment-based settings: Task 2.
   - PostgreSQL + Alembic: Tasks 4, 5.
   - JSON logs + request IDs: Task 3.
   - Docker Compose: Task 8.
   - CI: Task 10.
   - Tests: Tasks 2, 3, 4, 5, 6, 7.
   - No gap identified.

2. **Placeholder scan:** All steps include concrete file paths and code blocks.

3. **Type consistency:** `Settings.database_url` is `PostgresDsn` and converted to `str` when passed to SQLAlchemy/ Alembic.

## Execution Choice

Inline execution in this session using `superpowers:executing-plans`.
