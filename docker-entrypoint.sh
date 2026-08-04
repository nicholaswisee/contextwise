#!/bin/bash
set -e

echo "Running database migrations..."
uv run alembic upgrade head

exec "$@"
