from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter

from src.tg_bot.filters import ChatTypeFilter
from src.tg_bot.handlers.callback_mapping import callback_action_mapping
from src.tg_bot.states.user import ThemeEdit, UserRegistration, UserTheme

from . import group, group_handle, payment, registration, theme, report, restore


def prepare_router() -> Router:
    user_router = Router()
    user_router.message.filter(ChatTypeFilter("private"))

    user_router.message.register(group.groups_command, Command("groups"))
    user_router.message.register(theme.themes_command, Command("themes"))
    user_router.message.register(
        registration.start_registration,
        Command("registration"),
    )
    user_router.message.register(group_handle.handle_command, Command("handle"))
    user_router.message.register(payment.pay_command, Command("pay"))

    user_router.message.register(theme.name_theme, StateFilter(UserTheme.name))
    user_router.message.register(
        theme.description_theme,
        StateFilter(UserTheme.description),
    )
    user_router.message.register(theme.gpt_theme, StateFilter(UserTheme.gpt))
    user_router.message.register(
        registration.phone_registration,
        StateFilter(UserRegistration.phone),
    )
    user_router.message.register(theme.edit_theme_field, ThemeEdit.edit_name)
    user_router.message.register(theme.edit_theme_field, ThemeEdit.edit_description)
    user_router.message.register(theme.edit_theme_field, ThemeEdit.edit_prompt)
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
        registration.tg_code_registration,
        StateFilter(UserRegistration.tg_code),
    )

    user_router.message.register(
        payment.process_amount, StateFilter("waiting_for_amount")
    )

    user_router.message.register(report.report_command, Command("report"))
    user_router.message.register(
        report.generate_report, StateFilter("waiting_for_report_period")
    )

    user_router.message.register(restore.start_restore, Command("restore_session"))
    user_router.message.register(restore.restore_code, StateFilter("waiting_for_restore_code"))
    user_router.message.register(restore.restore_password, StateFilter("waiting_for_restore_password"))

    for handler, filter_ in callback_action_mapping:
        user_router.callback_query.register(handler, filter_)

    return user_router
