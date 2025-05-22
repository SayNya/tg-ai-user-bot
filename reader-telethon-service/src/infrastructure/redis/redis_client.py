from typing import Any

from redis.asyncio import Redis


class RedisClient:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> bytes | None:
        try:
            return await self._redis.get(key)
        except Exception as e:
            raise e

    async def set(self, key: str, value: Any, expire: int | None = None) -> None:
        try:
            await self._redis.set(key, value, ex=expire)
        except Exception as e:
            raise e

    async def hset(self, name: str, mapping: dict[str, Any]) -> None:
        try:
            await self._redis.hset(name, mapping=mapping)
        except Exception as e:
            raise e

    async def hgetall(self, name: str) -> dict[str, bytes]:
        try:
            return await self._redis.hgetall(name)
        except Exception as e:
            raise e

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except Exception as e:
            raise e
