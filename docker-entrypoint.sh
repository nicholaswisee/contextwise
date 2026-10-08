#!/bin/bash
set -e

echo "Running database migrations..."
uv run --no-dev alembic upgrade head

exec "$@"
