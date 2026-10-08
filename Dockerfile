FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends make && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock .python-version ./
RUN pip install uv
COPY src ./src
COPY alembic.ini ./

RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uv", "run", "--no-dev", "uvicorn", "--factory", "contextwise.api.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
