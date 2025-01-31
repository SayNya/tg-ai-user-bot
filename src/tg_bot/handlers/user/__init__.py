from aiogram import F, Router
from aiogram.filters import Command, CommandStart, MagicData, StateFilter

from src.models import user as user
from src.tg_bot.filters import ChatTypeFilter
from src.tg_bot.keyboards.inline import callbacks
from src.tg_bot.states.user import UserRegistration, UserTheme

from . import group, group_handle, registration, start, theme


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
        theme.description_theme,
        StateFilter(UserTheme.description),
    )

    user_router.message.register(group_handle.handle_command, Command("handle"))
    user_router.callback_query.register(
        group_handle.handle_theme,
        callbacks.HandleGroupTheme.filter(F.action == "handle_theme"),
    )
    user_router.callback_query.register(
        group_handle.save_handle,
        callbacks.HandleGroupTheme.filter(F.action == "save"),
    )

    user_router.message.register(
        registration.start_registration,
        Command("registration"),
    )
    user_router.message.register(
        registration.phone_registration,
        StateFilter(UserRegistration.phone),
    )
    user_router.message.register(
        registration.api_id_registration,
        StateFilter(UserRegistration.api_id),
    )
    user_router.message.register(
        registration.api_hash_registration,
        StateFilter(UserRegistration.api_hash),
    )
    user_router.message.register(
        registration.have_password,
        StateFilter(UserRegistration.have_password),
    )
    user_router.message.register(
        registration.password_registration,
        StateFilter(UserRegistration.password),
    )
    user_router.message.register(
        registration.register_client,
        StateFilter(UserRegistration.have_password),
    )
    user_router.message.register(
        registration.tg_code_registration,
        StateFilter(UserRegistration.tg_code),
    )
    return user_router
