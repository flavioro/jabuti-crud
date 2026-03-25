from __future__ import annotations

import logging
from collections.abc import Generator

from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
LOGGER = logging.getLogger(__name__)
engine = create_engine(settings.sqlalchemy_database_uri, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
_redis_client: Redis | None = None


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis() -> Redis | None:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True,
            )
            _redis_client.ping()
        except RedisError as exc:
            LOGGER.warning("redis_unavailable error=%s", exc)
            _redis_client = None
    return _redis_client


def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None
