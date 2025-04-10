import asyncio
import logging
from typing import TYPE_CHECKING

import httpx
import tenacity
from openai import AsyncOpenAI

from src import utils
from src.context import AppContext
from src.data import config
from src.tg_bot import tg_bot
from src.user_bot import utils as user_bot_utils

if TYPE_CHECKING:
    import structlog


def setup_logging(context: AppContext) -> None:
    logging.getLogger("httpcore").propagate = False
    logging.getLogger("httpx").propagate = False
    logging.getLogger("openai").propagate = False

    context["business_logger"] = utils.logging.setup_logger().bind(type="aiogram")
    context["db_logger"] = utils.logging.setup_logger().bind(type="db")

    context["aiogram_logger"] = utils.logging.setup_logger().bind(type="aiogram")
    context["telethon_logger"] = utils.logging.setup_logger().bind(type="telethon")


async def create_db_connection(context: AppContext) -> None:
    logger: structlog.typing.FilteringBoundLogger = context["business_logger"]

    logger.debug("Connecting to PostgreSQL", db="main")
    try:
        db_pool = await utils.connect_to_services.wait_postgres(
            logger=context["db_logger"],
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
        logger.debug("Successfully connected to PostgreSQL", db="main")
    context["db_pool"] = db_pool


async def initialize_shared_resources() -> AppContext:
    context = AppContext()

    setup_logging(context)
    await create_db_connection(context)
    context["user_clients"] = {}
    context["openai"] = AsyncOpenAI(
        api_key=config.CHAT_GPT_API,
        http_client=httpx.AsyncClient(proxy=config.PROXY),
    )
    context["modulbank_api"] = utils.modulbank_api.ModulBankApi(
        merchant_id=config.MODULBANK_MERCHANT_ID,
        secret_key=config.MODULBANK_SECRET,
        callback_url=f"{config.MODULBANK_HOST}/reader/modulbank",
        success_url="https://pay.modulbank.ru/success",
        testing=config.DEBUG,
    )
    return context


async def main() -> None:
    context = await initialize_shared_resources()

    aiogram_task = asyncio.create_task(tg_bot.run_aiogram(context))
    telethon_task = asyncio.create_task(user_bot_utils.setup_telethon_clients(context))

    await asyncio.gather(aiogram_task, telethon_task, return_exceptions=True)

    await context.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
