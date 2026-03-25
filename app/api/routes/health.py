from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db, get_redis
from app.schemas.user import HealthResponse

router = APIRouter(tags=["health"])
LOGGER = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse, summary="Healthcheck da aplicação")
def healthcheck(
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis),
) -> HealthResponse:
    settings = get_settings()
    db.scalar(text("SELECT 1"))

    cache_status = "ok"
    if redis_client is None:
        cache_status = "unavailable"
    else:
        try:
            redis_client.ping()
        except RedisError as exc:
            LOGGER.warning("health_cache_unavailable", extra={"error": str(exc)})
            cache_status = "unavailable"

    status = "ok" if cache_status == "ok" else "degraded"
    return HealthResponse(
        status=status,
        app=settings.app_name,
        version=settings.app_version,
        database="ok",
        cache=cache_status,
    )
