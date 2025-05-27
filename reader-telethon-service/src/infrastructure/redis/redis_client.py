from typing import Any

import structlog
from redis.asyncio import Redis


class RedisClient:
    def __init__(
        self,
        redis: Redis,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self._redis = redis
        self.logger = logger

    async def get(self, key: str) -> bytes | None:
        self.logger.debug("redis_get", key=key)
        try:
            value = await self._redis.get(key)
            self.logger.debug(
                "redis_get_success",
                key=key,
                value_exists=value is not None,
            )
            return value
        except Exception as e:
            self.logger.exception("redis_get_error", key=key, error=str(e))
            raise e

    async def set(self, key: str, value: Any, expire: int | None = None) -> None:
        self.logger.debug("redis_set", key=key, expire=expire)
        try:
            await self._redis.set(key, value, ex=expire)
            self.logger.debug("redis_set_success", key=key)
        except Exception as e:
            self.logger.exception("redis_set_error", key=key, error=str(e))
            raise e

    async def hset(self, name: str, mapping: dict[str, Any]) -> None:
        self.logger.debug("redis_hset", name=name, keys=list(mapping.keys()))
        try:
            await self._redis.hset(name, mapping=mapping)
            self.logger.debug("redis_hset_success", name=name)
        except Exception as e:
            self.logger.exception("redis_hset_error", name=name, error=str(e))
            raise e

    async def hgetall(self, name: str) -> dict[str, bytes]:
        self.logger.debug("redis_hgetall", name=name)
        try:
            result = await self._redis.hgetall(name)
            self.logger.debug(
                "redis_hgetall_success",
                name=name,
                keys=list(result.keys()),
            )
            return result
        except Exception as e:
            self.logger.exception("redis_hgetall_error", name=name, error=str(e))
            raise e

    async def delete(self, key: str) -> None:
        self.logger.debug("redis_delete", key=key)
        try:
            await self._redis.delete(key)
            self.logger.debug("redis_delete_success", key=key)
        except Exception as e:
            self.logger.exception("redis_delete_error", key=key, error=str(e))
            raise e

    async def expire(self, key: str, seconds: int) -> None:
        self.logger.debug("redis_expire", key=key, seconds=seconds)
        try:
            await self._redis.expire(key, seconds)
            self.logger.debug("redis_expire_success", key=key)
        except Exception as e:
            self.logger.exception("redis_expire_error", key=key, error=str(e))
            raise e
