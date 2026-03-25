import json
import logging
from typing import Any
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

LOGGER = logging.getLogger(__name__)


class CacheService:
    def __init__(self, redis_client: Redis | None, ttl_seconds: int) -> None:
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def list_key(limit: int, offset: int) -> str:
        return f"users:list:limit={limit}:offset={offset}"

    @staticmethod
    def detail_key(user_id: UUID) -> str:
        return f"users:detail:{user_id}"

    @property
    def available(self) -> bool:
        return self.redis_client is not None

    def get_json(self, key: str) -> dict[str, Any] | None:
        if self.redis_client is None:
            LOGGER.info("cache_unavailable_read", extra={"key": key})
            return None
        try:
            payload = self.redis_client.get(key)
            if payload is None:
                LOGGER.info("cache_miss", extra={"key": key})
                return None
            LOGGER.info("cache_hit", extra={"key": key})
            return json.loads(payload)
        except (RedisError, json.JSONDecodeError, TypeError) as exc:
            LOGGER.warning("cache_read_failed", extra={"key": key, "error": str(exc)})
            return None

    def set_json(self, key: str, value: dict[str, Any]) -> None:
        if self.redis_client is None:
            LOGGER.info("cache_unavailable_write", extra={"key": key})
            return
        try:
            self.redis_client.setex(key, self.ttl_seconds, json.dumps(value, default=str))
            LOGGER.info("cache_set", extra={"key": key})
        except RedisError as exc:
            LOGGER.warning("cache_write_failed", extra={"key": key, "error": str(exc)})

    def invalidate_pattern(self, pattern: str) -> int:
        if self.redis_client is None:
            LOGGER.info("cache_unavailable_invalidate", extra={"pattern": pattern})
            return 0
        try:
            deleted = 0
            for key in self.redis_client.scan_iter(match=pattern):
                deleted += int(self.redis_client.delete(key))
            LOGGER.info("cache_invalidate", extra={"pattern": pattern, "deleted": deleted})
            return deleted
        except RedisError as exc:
            LOGGER.warning("cache_invalidate_failed", extra={"pattern": pattern, "error": str(exc)})
            return 0

    def invalidate_list_cache(self) -> int:
        return self.invalidate_pattern("users:list:*")

    def invalidate_detail_cache(self, user_id: UUID) -> int:
        return self.invalidate_pattern(f"users:detail:{user_id}")

    def invalidate_users_cache(self, user_id: UUID | None = None) -> int:
        deleted = self.invalidate_list_cache()
        if user_id is not None:
            deleted += self.invalidate_detail_cache(user_id)
        return deleted
