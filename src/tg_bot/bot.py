from typing import TYPE_CHECKING

import tenacity
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from redis.asyncio import Redis

from src import utils
from src.tg_bot import handlers
from src.data import config
from src.tg_bot.middlewares import StructLoggingMiddleware

if TYPE_CHECKING:
    import asyncpg as asyncpg
    import redis
    import structlog


async def create_db_connections(dp: Dispatcher) -> None:
    logger: structlog.typing.FilteringBoundLogger = dp["business_logger"]

    logger.debug("Connecting to PostgreSQL", db="main")
    try:
        db_pool = await utils.connect_to_services.wait_postgres(
            logger=dp["db_logger"],
            host=config.PG_HOST,
            port=config.PG_PORT,
            user=config.PG_USER,
            password=config.PG_PASSWORD,
            database=config.PG_DATABASE,
        )
    except tenacity.RetryError:
        logger.exception("Failed to connect to PostgreSQL", db="main")
        exit(1)
    else:
        logger.debug("Succesfully connected to PostgreSQL", db="main")
    dp["db_pool"] = db_pool


async def close_db_connections(dp: Dispatcher) -> None:
    if "db_pool" in dp.workflow_data:
        db_pool: asyncpg.Pool = dp["db_pool"]
        await db_pool.close()
    if "cache_pool" in dp.workflow_data:
        cache_pool: redis.asyncio.Redis = dp["cache_pool"]  # type: ignore[type-arg]
        await cache_pool.close()


def setup_handlers(dp: Dispatcher) -> None:
    dp.include_router(handlers.user.prepare_router())


def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.outer_middleware(StructLoggingMiddleware(logger=dp["aiogram_logger"]))


def setup_logging(dp: Dispatcher) -> None:
    dp["aiogram_logger"] = utils.logging.setup_logger().bind(type="aiogram")
    dp["db_logger"] = utils.logging.setup_logger().bind(type="db")
    dp["business_logger"] = utils.logging.setup_logger().bind(type="business")


async def setup_aiogram(dp: Dispatcher) -> None:
    setup_logging(dp)
    logger = dp["aiogram_logger"]
    logger.debug("Configuring aiogram")
    await create_db_connections(dp)
    setup_handlers(dp)
    setup_middlewares(dp)
    logger.info("Configured aiogram")


async def aiogram_on_startup_polling(dispatcher: Dispatcher) -> None:
    await setup_aiogram(dispatcher)
    dispatcher["aiogram_logger"].info("Started polling")


async def aiogram_on_shutdown_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    dispatcher["aiogram_logger"].debug("Stopping polling")
    await close_db_connections(dispatcher)
    await bot.session.close()
    await dispatcher.storage.close()
    dispatcher["aiogram_logger"].info("Stopped polling")


async def main(user_bot) -> None:
    aiogram_session_logger = utils.logging.setup_logger().bind(type="aiogram_session")

    bot = Bot(
        config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    storage = (
        RedisStorage(
            redis=Redis(
                host=config.FSM_HOST,
                password=config.FSM_PASSWORD,
                port=config.FSM_PORT,
                db=0,
            ),
            key_builder=DefaultKeyBuilder(with_bot_id=True),
        )
        if not config.DEBUG
        else None
    )

    dp = Dispatcher(storage=storage)
    dp["aiogram_session_logger"] = aiogram_session_logger
    dp["user_bot"] = user_bot

    dp.startup.register(aiogram_on_startup_polling)
    dp.shutdown.register(aiogram_on_shutdown_polling)
    await dp.start_polling(bot)
