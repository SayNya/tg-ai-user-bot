import asyncio
from typing import TYPE_CHECKING

import tenacity

from src import utils
from src.data import config
from src.tg_bot import tg_bot

if TYPE_CHECKING:
    import structlog


def setup_logging(context: utils.shared_context.AppContext) -> None:
    context["business_logger"] = utils.logging.setup_logger().bind(type="aiogram")
    context["db_logger"] = utils.logging.setup_logger().bind(type="db")

    context["aiogram_logger"] = utils.logging.setup_logger().bind(type="aiogram")
    context["telethon_logger"] = utils.logging.setup_logger().bind(type="telethon")


async def create_db_connection(context: utils.shared_context.AppContext) -> None:
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
        logger.debug("Succesfully connected to PostgreSQL", db="main")
    context["db_pool"] = db_pool


async def initialize_shared_resources() -> utils.shared_context.AppContext:
    context = utils.shared_context.AppContext()

    setup_logging(context)
    await create_db_connection(context)
    context["user_clients"] = {}

    return context


async def main() -> None:

    context = await initialize_shared_resources()

    aiogram_task = asyncio.create_task(tg_bot.run_aiogram(context))
    # telethon_task = asyncio.create_task(user_bot.setup_telethon_clients(context))

    await asyncio.gather(aiogram_task, return_exceptions=True)

    await context.cleanup()


if __name__ == "__main__":
    asyncio.ensure_future(main())
    asyncio.get_event_loop().run_forever()
