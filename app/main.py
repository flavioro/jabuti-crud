from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.users import router as users_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.migrations import run_migrations
from app.db.session import close_redis, engine, get_redis

settings = get_settings()
configure_logging(settings.log_level, settings.log_json)
LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.run_migrations_on_startup:
        run_migrations()

    if settings.environment != "test":
        redis_client = get_redis()
        app.state.redis = redis_client
        if redis_client is None:
            LOGGER.warning("application_started_without_cache", extra={"environment": settings.environment})

    LOGGER.info("application_started", extra={"environment": settings.environment})
    try:
        yield
    finally:
        if settings.environment != "test":
            close_redis()
            engine.dispose()
        LOGGER.info("application_stopped", extra={"environment": settings.environment})


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API de usuários para o desafio Jabuti com FastAPI, PostgreSQL, Redis, logs, "
        "migrações Alembic e Swagger."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started_at = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    LOGGER.info(
        "request_completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": elapsed_ms,
        },
    )
    return response


app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(users_router, prefix=settings.api_prefix)
