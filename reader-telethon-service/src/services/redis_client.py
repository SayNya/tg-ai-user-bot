from redis.asyncio import Redis

from src.config import settings

redis: Redis = Redis(
    host=settings.redis.host,
    port=settings.redis.port,
    db=settings.redis.db,
    decode_responses=True,
)
