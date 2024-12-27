from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter, Command

from src.tg_bot.filters import ChatTypeFilter

from . import start, group, theme, group_handle
from src.tg_bot.keyboards.inline import callbacks
from ...states.user import UserTheme


def prepare_router() -> Router:
    user_router = Router()
    user_router.message.filter(ChatTypeFilter("private"))

    user_router.message.register(start.start, CommandStart())

    user_router.message.register(group.groups_command, Command("groups"))
    user_router.callback_query.register(
        group.choose_group_to_add,
        callbacks.GroupCallbackFactory.filter(F.action == "add"),
    )
    user_router.callback_query.register(
        group.add_group,
        callbacks.ChangeGroupCallbackFactory.filter(F.action == "add"),
    )
    user_router.callback_query.register(
        group.choose_group_to_delete,
        callbacks.GroupCallbackFactory.filter(F.action == "delete"),
    )
    user_router.callback_query.register(
        group.delete_group,
        callbacks.ChangeGroupCallbackFactory.filter(F.action == "delete"),
    )

    user_router.message.register(theme.start_theme, Command("themes"))
    user_router.message.register(theme.name_theme, StateFilter(UserTheme.name))
    user_router.message.register(
        theme.description_theme, StateFilter(UserTheme.description)
    )

    user_router.message.register(group_handle.handle_command, Command("handle"))
    user_router.callback_query.register(
        group_handle.handle_theme,
        callbacks.HandleGroupTheme.filter(F.action == "handle_theme"),
    )
    user_router.callback_query.register(
        group_handle.save_handle, callbacks.HandleGroupTheme.filter(F.action == "save")
    )

    return user_router
