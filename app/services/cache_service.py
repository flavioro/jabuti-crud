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
            LOGGER.info("cache_unavailable_read key=%s", key)
            return None
        try:
            payload = self.redis_client.get(key)
            if payload is None:
                LOGGER.info("cache_miss key=%s", key)
                return None
            LOGGER.info("cache_hit key=%s", key)
            return json.loads(payload)
        except (RedisError, json.JSONDecodeError, TypeError) as exc:
            LOGGER.warning("cache_read_failed key=%s error=%s", key, exc)
            return None

    def set_json(self, key: str, value: dict[str, Any]) -> None:
        if self.redis_client is None:
            LOGGER.info("cache_unavailable_write key=%s", key)
            return
        try:
            self.redis_client.setex(key, self.ttl_seconds, json.dumps(value, default=str))
            LOGGER.info("cache_set key=%s", key)
        except RedisError as exc:
            LOGGER.warning("cache_write_failed key=%s error=%s", key, exc)

    def invalidate_pattern(self, pattern: str) -> int:
        if self.redis_client is None:
            LOGGER.info("cache_unavailable_invalidate pattern=%s", pattern)
            return 0
        try:
            deleted = 0
            for key in self.redis_client.scan_iter(match=pattern):
                deleted += int(self.redis_client.delete(key))
            LOGGER.info("cache_invalidate pattern=%s deleted=%s", pattern, deleted)
            return deleted
        except RedisError as exc:
            LOGGER.warning("cache_invalidate_failed pattern=%s error=%s", pattern, exc)
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
