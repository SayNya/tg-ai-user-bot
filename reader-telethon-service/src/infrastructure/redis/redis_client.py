from redis.asyncio import Redis


class RedisClient:
    def __init__(self, redis: Redis):
        self._redis = redis

    async def get(self, key: str):
        try:
            value = await self._redis.get(key)
            return value
        except Exception as e:
            raise e

    async def set(self, key: str, value, expire: int = None):
        try:
            await self._redis.set(key, value, ex=expire)
        except Exception as e:
            raise e

    async def hset(self, name: str, mapping: dict):
        try:
            await self._redis.hset(name, mapping=mapping)
        except Exception as e:
            raise e

    async def hgetall(self, name: str):
        try:
            result = await self._redis.hgetall(name)
            return result
        except Exception as e:
            raise e

    async def delete(self, key: str):
        try:
            await self._redis.delete(key)
        except Exception as e:
            raise e
