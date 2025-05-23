import asyncio
import logging
import sys
from functools import partial
from typing import TYPE_CHECKING

import tenacity
from aio_pika import RobustConnection, connect_robust
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import BotCommand
from redis.asyncio import Redis

from src import utils
from src.data import settings
from src.rabbitmq import registry
from src import handlers
from src.middlewares import DbSessionMiddleware, StructLoggingMiddleware

if TYPE_CHECKING:
    import structlog
    from sqlalchemy.ext.asyncio import AsyncEngine


async def create_db_connections(dp: Dispatcher) -> None:
    logger: structlog.typing.FilteringBoundLogger = dp["business_logger"]

    logger.debug("Connecting to PostgreSQL", db="main")
    try:
        engine, sessionmaker = await utils.connect_to_services.wait_postgres(
            logger=dp["db_logger"],
            url=settings.database.url,
        )
    except tenacity.RetryError:
        logger.exception("Failed to connect to PostgreSQL", db="main")
        sys.exit(1)
    else:
        logger.debug("Successfully connected to PostgreSQL", db="main")

    dp["db_engine"] = engine
    dp["sessionmaker"] = sessionmaker

    if settings.use_cache:
        logger.debug("Connecting to Redis")
        try:
            redis_pool = await utils.connect_to_services.wait_redis_pool(
                logger=dp["cache_logger"],
                host=settings.cache.host,
                port=settings.cache.port,
                database=settings.cache.db,
            )
        except tenacity.RetryError:
            logger.exception("Failed to connect to Redis")
            sys.exit(1)
        else:
            logger.debug("Successfully connected to Redis")
        dp["cache_pool"] = redis_pool


async def close_db_connections(dp: Dispatcher) -> None:
    if "db_engine" in dp.workflow_data:
        db_engine: AsyncEngine = dp["db_engine"]
        await db_engine.dispose()
    if "publisher_conn" in dp.workflow_data:
        publisher_conn: RobustConnection = dp["publisher_conn"]
        await publisher_conn.close()
    if "cache_pool" in dp.workflow_data:
        cache_pool: Redis = dp["cache_pool"]
        await cache_pool.close()


def setup_handlers(dp: Dispatcher) -> None:
    dp.include_router(handlers.user.prepare_router())


def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.outer_middleware(StructLoggingMiddleware(logger=dp["aiogram_logger"]))
    dp.update.middleware(DbSessionMiddleware(sessionmaker=dp["sessionmaker"]))


def setup_logging(dp: Dispatcher) -> None:
    for noisy in ["httpcore", "httpx", "openai", "aiogram"]:
        logging.getLogger(noisy).setLevel(logging.CRITICAL + 1)

    dp["business_logger"] = utils.logging.setup_logger().bind(type="aiogram")
    dp["db_logger"] = utils.logging.setup_logger().bind(type="db")
    dp["cache_logger"] = utils.logging.setup_logger().bind(type="cache")

    dp["aiogram_logger"] = utils.logging.setup_logger().bind(type="aiogram")


async def setup_aiogram(dp: Dispatcher) -> None:
    setup_logging(dp)
    logger = dp["aiogram_logger"]
    logger.debug("Configuring aiogram")
    await create_db_connections(dp)
    setup_handlers(dp)
    setup_middlewares(dp)

    dp["modulbank_api"] = utils.modulbank_api.ModulBankApi(
        merchant_id=settings.modulbank.merchant_id,
        secret_key=settings.modulbank.secret,
        callback_url=f"{settings.modulbank.host}/reader/modulbank",
        success_url="https://pay.modulbank.ru/success",
        testing=settings.debug,
    )

    publisher_conn = await connect_robust(settings.rabbitmq.url)
    publisher_channel = await publisher_conn.channel()
    dp["publisher_conn"] = publisher_conn
    dp["publisher_channel"] = publisher_channel

    logger.info("Configured aiogram")


async def setup_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Старт"),
            BotCommand(command="groups", description="Настройка групп"),
            BotCommand(command="themes", description="Настройка тем"),
            BotCommand(command="handle", description="Привязка тем к группам"),
            BotCommand(command="report", description="Генерация отчёта"),
            BotCommand(command="registration", description="Регистрация аккаунта"),
            BotCommand(command="pay", description="Оплата"),
            BotCommand(command="restore_session", description="Восстановить сессию"),
        ],
    )


async def setup_rabbitmq_consumer(bot: Bot, dispatcher: Dispatcher) -> None:
    connection = await connect_robust(settings.rabbitmq.url)
    channel = await connection.channel()

    for queue_name, handler in registry.items():
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.consume(partial(handler, bot=bot, dispatcher=dispatcher))


async def aiogram_on_startup_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    await setup_commands(bot)
    await setup_aiogram(dispatcher)
    await setup_rabbitmq_consumer(bot, dispatcher)
    dispatcher["aiogram_logger"].info("Started polling")


async def aiogram_on_shutdown_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    dispatcher["aiogram_logger"].debug("Stopping polling")
    await close_db_connections(dispatcher)
    await bot.session.close()
    await dispatcher.storage.close()
    dispatcher["aiogram_logger"].info("Stopped polling")


def main() -> None:
    aiogram_session_logger = utils.logging.setup_logger().bind(type="aiogram_session")

    bot = Bot(
        settings.bot.token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    dp = Dispatcher(
        storage=RedisStorage(
            redis=Redis(
                host=settings.storage.host,
                port=settings.storage.port,
                db=settings.storage.db,
            ),
            key_builder=DefaultKeyBuilder(with_bot_id=True),
        ),
    )

    dp["aiogram_session_logger"] = aiogram_session_logger
    dp.startup.register(aiogram_on_startup_polling)
    dp.shutdown.register(aiogram_on_shutdown_polling)
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
