from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter, Command

from src.tg_bot.filters import ChatTypeFilter, TextFilter as TextFilter

from . import start
from src.tg_bot.keyboards.inline import callbacks


def prepare_router() -> Router:
    user_router = Router()
    user_router.message.filter(ChatTypeFilter("private"))

    user_router.message.register(start.start, CommandStart())
    user_router.message.register(start.groups_command, Command("groups"))

    user_router.callback_query.register(
        start.choose_group_to_add,
        callbacks.GroupCallbackFactory.filter(F.action == "add"),
    )
    user_router.callback_query.register(
        start.add_group, callbacks.ChangeGroupCallbackFactory.filter(F.action == "add"),
    )

    user_router.callback_query.register(
        start.choose_group_to_delete,
        callbacks.GroupCallbackFactory.filter(F.action == "delete"),
    )
    user_router.callback_query.register(
        start.delete_group, callbacks.ChangeGroupCallbackFactory.filter(F.action == "delete")
    )
    # user_router.message.register(
    #     start.start,
    #     TextFilter("🏠В главное меню"),
    #     StateFilter(src.tg_bot.states.user.UserMainMenu.menu),
    # )

    return user_router
