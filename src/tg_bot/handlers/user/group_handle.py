import asyncpg
import structlog
from aiogram import types

from src.db.repositories import GroupThemeRepository
from src.tg_bot.keyboards.inline import callbacks, user
from src.user_bot.bot import UserClient


async def handle_command(
    msg: types.Message,
    user_clients: dict[int, UserClient],
) -> None:
    if msg.from_user is None:
        return

    client = user_clients.get(msg.from_user.id)
    groups = await client.get_active_groups()

    await msg.answer(
        "Выберите группу:",
        reply_markup=user.handle.HandleButtons().groups_buttons(groups=groups),
    )


async def handle_theme(
    cb: types.CallbackQuery,
    callback_data: callbacks.HandleGroupTheme,
    user_clients: dict[int, UserClient],
) -> None:
    if cb.from_user is None:
        return

    client = user_clients.get(cb.from_user.id)
    themes = await client.get_themes()

    await cb.message.answer(
        "Выберите тему:",
        reply_markup=user.handle.HandleButtons().themes_buttons(
            themes=themes,
            group_id=callback_data.group_id,
        ),
    )
    await cb.answer()


async def save_handle(
    cb: types.CallbackQuery,
    callback_data: callbacks.HandleGroupTheme,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
) -> None:
    if cb.from_user is None:
        return

    await GroupThemeRepository(db_pool, db_logger).add_group_theme(
        chat_id=callback_data.group_id,
        theme_id=callback_data.theme_id,
        user_id=cb.from_user.id,
    )

    await cb.message.answer("Тема привязана к группе")
    await cb.answer()
