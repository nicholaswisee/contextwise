from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

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

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
            },
        )

    return app
