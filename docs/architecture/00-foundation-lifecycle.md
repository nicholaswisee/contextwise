# Milestone 0 — Startup and Shutdown Lifecycle

```mermaid
flowchart TD
    A[Uvicorn starts] --> B[create_app builds FastAPI application]
    B --> C[Lifespan startup]
    C --> D[Load AppState and Settings]
    D --> E[Configure JSON logging]
    E --> F[Initialize database resources]
    F --> G[Serve HTTP requests]

    G --> H[RequestIDMiddleware increments active request count]
    H --> I[FastAPI resolves dependencies and runs route]
    I --> J[Middleware returns response]
    J --> K[Middleware decrements active request count]

    G --> L[Server begins shutdown]
    L --> M[Lifespan resumes after yield]
    M --> N[Wait until active request count reaches zero]
    N --> O[Dispose SQLAlchemy engine]
    O --> P[Process exits]
```

## Operational notes

- `/health/live` checks only that the API process can answer.
- `/health/ready` checks PostgreSQL connectivity.
- Shutdown waits for in-flight requests before disposing the database engine.
- Alembic migrations run before the container starts Uvicorn through `docker-entrypoint.sh`.
