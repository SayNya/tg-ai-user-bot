import asyncio
import logging

from httpx import AsyncClient
from openai import AsyncOpenAI
from pyrogram import filters
from pyrogram.handlers import MessageHandler

from src import utils
from src.data import config
from src.tg_bot import tg_bot_main
from src.user_bot import bot, handlers
from src.user_bot.utils import UserBot


async def configure_pyrogram(my_bot, handlersa):
    db_logger = utils.logging.setup_logger().bind(type="db")
    pool = await utils.connect_to_services.wait_postgres(
        logger=db_logger,
        host=config.PG_HOST,
        port=config.PG_PORT,
        user=config.PG_USER,
        password=config.PG_PASSWORD,
        database=config.PG_DATABASE,
    )
    user_bot = UserBot(my_bot, pool, db_logger)

    my_bot.db_pool = pool
    my_bot.db_logger = db_logger

    client = AsyncOpenAI(
        api_key=config.CHAT_GPT_API, http_client=AsyncClient(proxy=config.PROXY)
    )
    my_bot.openai_client = client

    pyrogram_logger = logging.getLogger("pyrogram")
    pyrogram_logger.propagate = False

    for handler in handlersa:
        my_bot.add_handler(MessageHandler(handler, filters=filters.group))

    return user_bot


async def main():
    user_bot = await configure_pyrogram(bot.app, [handlers.my_handler])

    task1 = await asyncio.create_task(user_bot.client.start())
    task2 = await asyncio.create_task(tg_bot_main(user_bot))
    await asyncio.gather(task1, task2, return_exceptions=True)


if __name__ == "__main__":
    asyncio.ensure_future(main())
    asyncio.get_event_loop().run_forever()
