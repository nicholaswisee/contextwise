.PHONY: install test test-integration lint format type check migrate up down test-db-up test-db-down

PYTHON ?= python3
TEST_DATABASE_URL ?= postgresql+asyncpg://contextwise:contextwise@localhost:5434/contextwise_test

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
	docker compose up -d --wait --build

down:
	docker compose down
