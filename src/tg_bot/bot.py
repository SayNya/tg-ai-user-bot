from functools import partial
from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from src import utils
from src.data import config
from src.tg_bot import handlers
from src.tg_bot.middlewares import StructLoggingMiddleware

if TYPE_CHECKING:
    import structlog


def setup_handlers(dp: Dispatcher) -> None:
    dp.include_router(handlers.user.prepare_router())


def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.outer_middleware(StructLoggingMiddleware(logger=dp["aiogram_logger"]))


async def setup_aiogram(
    dp: Dispatcher,
    context: utils.shared_context.AppContext,
) -> None:
    dp["aiogram_logger"] = context["aiogram_logger"]
    logger: structlog.typing.FilteringBoundLogger = dp["aiogram_logger"]

    logger.debug("Configuring aiogram")

    dp["db_pool"] = context["db_pool"]
    dp["db_logger"] = context["db_logger"]
    dp["user_clients"] = context["user_clients"]
    dp["context"] = context

    setup_handlers(dp)
    setup_middlewares(dp)

    logger.info("Configured aiogram")


async def aiogram_on_startup_polling(
    dispatcher: Dispatcher,
    context: utils.shared_context.AppContext,
) -> None:
    await setup_aiogram(dispatcher, context)
    dispatcher["aiogram_logger"].info("Started polling")


async def aiogram_on_shutdown_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    dispatcher["aiogram_logger"].debug("Stopping polling")
    await bot.session.close()
    await dispatcher.storage.close()
    dispatcher["aiogram_logger"].info("Stopped polling")


async def setup_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Старт"),
            BotCommand(command="groups", description="Настройка групп"),
            BotCommand(command="themes", description="Настройка тем"),
            BotCommand(command="handle", description="Привязка тем к группам"),
            BotCommand(command="registration", description="Регистрация аккаунта"),
        ],
    )


async def run_aiogram(context: utils.shared_context.AppContext) -> None:
    bot = Bot(
        config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    await setup_commands(bot)

    # storage = (
    #     RedisStorage(
    #         redis=Redis(
    #             host=config.FSM_HOST,
    #             password=config.FSM_PASSWORD,
    #             port=config.FSM_PORT,
    #             db=0,
    #         ),
    #         key_builder=DefaultKeyBuilder(with_bot_id=True),
    #     )
    #     if not config.DEBUG
    #     else None
    # )

    storage = None

    dp = Dispatcher(storage=storage)

    dp.startup.register(partial(aiogram_on_startup_polling, context=context))
    dp.shutdown.register(aiogram_on_shutdown_polling)
    await dp.start_polling(bot)
