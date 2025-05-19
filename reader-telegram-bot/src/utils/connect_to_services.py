import json

import orjson
import structlog
import tenacity
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from tenacity import _utils

from src.data.config import settings

TIMEOUT_BETWEEN_ATTEMPTS = 2
MAX_TIMEOUT = 30


def before_log(retry_state: tenacity.RetryCallState) -> None:
    if retry_state.outcome is None:
        return
    if retry_state.outcome.failed:
        verb, value = "raised", retry_state.outcome.exception()
    else:
        verb, value = "returned", retry_state.outcome.result()
    logger = retry_state.kwargs["logger"]
    logger.info(
        "Retrying %r in %.2f seconds as it %s %r",
        _utils.get_callback_name(retry_state.fn),  # type: ignore[arg-type]
        retry_state.next_action.sleep,  # type: ignore[union-attr]
        verb,
        value,
        extra={
            "callback": _utils.get_callback_name(retry_state.fn),  # type: ignore[arg-type]
            "sleep": retry_state.next_action.sleep,  # type: ignore[union-attr]
            "verb": verb,
            "value": value,
        },
    )


def after_log(retry_state: tenacity.RetryCallState) -> None:
    logger = retry_state.kwargs["logger"]
    logger.info(
        "Finished call to %r after %.2f, this was the %s time calling it.",
        _utils.get_callback_name(retry_state.fn),  # type: ignore[arg-type]
        retry_state.seconds_since_start,
        _utils.to_ordinal(retry_state.attempt_number),
        extra={
            "callback": _utils.get_callback_name(retry_state.fn),  # type: ignore[arg-type]
            "time": retry_state.seconds_since_start,
            "attempt": _utils.to_ordinal(retry_state.attempt_number),
        },
    )


@tenacity.retry(
    wait=tenacity.wait_fixed(TIMEOUT_BETWEEN_ATTEMPTS),
    stop=tenacity.stop_after_delay(MAX_TIMEOUT),
    before_sleep=before_log,
    after=after_log,
)
async def wait_postgres(
    logger: structlog.typing.FilteringBoundLogger,
    url: str,
) -> tuple[AsyncEngine, async_sessionmaker]:
    engine = create_async_engine(
        url=url,
        json_serializer=json.dumps,
        json_deserializer=orjson.loads,
        echo=(bool(settings.debug)),
    )
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async with sessionmaker() as session:
        result = await session.execute(text("SELECT version() as ver;"))
        version = result.scalar()

    logger.debug("Connected to PostgreSQL.", version=version)

    return engine, sessionmaker


@tenacity.retry(
    wait=tenacity.wait_fixed(TIMEOUT_BETWEEN_ATTEMPTS),
    stop=tenacity.stop_after_delay(MAX_TIMEOUT),
    before_sleep=before_log,
    after=after_log,
)
async def wait_redis_pool(
    *,
    logger: structlog.typing.FilteringBoundLogger,
    host: str,
    port: int,
    database: int,
) -> Redis:
    redis_connection: Redis = Redis(
        host=host,
        port=port,
        db=database,
        auto_close_connection_pool=True,
        decode_responses=True,
        protocol=3,
        socket_timeout=10,  # limits any command to 10 seconds as per https://github.com/redis/redis-py/issues/722
        socket_keepalive=True,  # tries to keep connection alive, not 100% guarantee
    )
    version = await redis_connection.info("server")
    logger.debug("Connected to Redis.", version=version["redis_version"])
    return redis_connection
