import asyncpg
import structlog
from aiogram import types

from src.db.repositories import ChatRepository
from src.tg_bot.keyboards.inline import callbacks, user
from src.user_bot.bot import UserClient


async def groups_command(
    msg: types.Message,
) -> None:
    if msg.from_user is None:
        return

    m = "Выберите действие:"
    await msg.answer(m, reply_markup=user.group.GroupButtons().main())


async def choose_group_to_add(
    cb: types.CallbackQuery,
    user_clients: dict[int, UserClient],
) -> None:
    if cb.from_user is None:
        return

    client = user_clients.get(cb.from_user.id)
    if not client:
        return

    groups = await client.get_all_groups(limit=10)

    await cb.message.answer(
        "Выберите группу для добавления",
        reply_markup=user.group.GroupButtons().groups(groups, "add"),
    )

    await cb.answer()


async def add_group(
    cb: types.CallbackQuery,
    callback_data: callbacks.ChangeGroupCallbackFactory,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
) -> None:
    if cb.from_user is None or cb.message is None:
        return

    await ChatRepository(db_pool, db_logger).add_chat(
        callback_data.id,
        callback_data.name,
        cb.from_user.id,
    )
    await cb.message.answer("Группа успешно добавлена в обработку")
    await cb.message.delete()


async def choose_group_to_delete(
    cb: types.CallbackQuery,
    user_bot,
) -> None:
    if cb.from_user is None:
        return

    groups = await user_bot.get_active_groups()
    await cb.message.answer(
        "Выберите группу для удаления",
        reply_markup=user.group.GroupButtons().groups(groups, "delete"),
    )

    await cb.answer()


async def delete_group(
    cb: types.CallbackQuery,
    callback_data: callbacks.ChangeGroupCallbackFactory,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
) -> None:
    if cb.from_user is None:
        return

    await ChatRepository(db_pool, db_logger).deactivate_chat(
        callback_data.id,
        cb.from_user.id,
    )
    await cb.message.answer("Группа успешно удалена из обработки")
