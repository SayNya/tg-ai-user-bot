import asyncpg
import structlog
from aiogram import types
from aiogram.fsm.context import FSMContext

from src.db.repositories import ChatRepository
from src.tg_bot.keyboards.inline import callbacks, user
from src.user_bot.bot import UserClient


async def groups_command(
    msg: types.Message,
    state: FSMContext,
) -> None:
    if msg.from_user is None:
        return

    await state.clear()
    m = "Выберите действие:"
    await msg.answer(m, reply_markup=user.group.GroupButtons().main())


async def choose_group_to_add(
    cb: types.CallbackQuery,
    callback_data: callbacks.GroupCallbackFactory,
    user_clients: dict[int, UserClient],
    state: FSMContext,
) -> None:
    if cb.from_user is None:
        return

    client = user_clients.get(cb.from_user.id)
    if not client:
        return

    data = await state.get_data()
    groups = data.get("groups")
    if groups is None:
        groups = await client.get_all_groups(limit=50)
        await state.update_data(groups=groups)

    page = callback_data.page
    reply_markup = user.group.GroupButtons().groups(groups, "add", page)
    await cb.message.edit_text(
        "Выберите группу для добавления",
        reply_markup=reply_markup,
    )
    await cb.answer()


async def add_group(
    cb: types.CallbackQuery,
    callback_data: callbacks.ChangeGroupCallbackFactory,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
    user_clients: dict[int, UserClient],
    state: FSMContext,
) -> None:
    if cb.from_user is None or cb.message is None:
        return

    data = await state.get_data()
    groups = data.get("groups", [])

    # Find the group by its ID
    group_name = None
    for group in groups:
        if group.id == callback_data.id:
            group_name = group.name
            break

    if not group_name:
        # Refresh the group list as a fallback
        client = user_clients.get(cb.from_user.id)
        if client:
            groups = await client.get_all_groups(limit=50)
            await state.update_data(groups=groups)
            for group in groups:
                if group.id == callback_data.id:
                    group_name = group.name
                    break

    if not group_name:
        await cb.message.answer("Ошибка: информация о группе не найдена.")
        return

    chat = await ChatRepository(db_pool, db_logger).get_group_by_id(
        callback_data.id, cb.from_user.id
    )
    if not chat:
        await ChatRepository(db_pool, db_logger).add_chat(
            callback_data.id,
            group_name,
            cb.from_user.id,
        )
    else:
        await ChatRepository(db_pool, db_logger).activate_chat(
            callback_data.id,
            cb.from_user.id,
        )
    await cb.message.answer("Группа успешно добавлена в обработку")
    await cb.message.delete()


async def choose_group_to_delete(
    cb: types.CallbackQuery,
    user_clients: dict[int, UserClient],
    state: FSMContext,
    page: int = 0,
) -> None:
    if cb.from_user is None:
        return

    client = user_clients.get(cb.from_user.id)
    if not client:
        return

    # Fetch groups only once
    data = await state.get_data()
    groups = data.get("active_groups")
    if groups is None:
        groups = await client.get_active_groups()  # Fetch active groups
        await state.update_data(active_groups=groups)

    # Display paginated groups
    reply_markup = user.group.GroupButtons().groups(groups, "delete", page)
    await cb.message.edit_text(
        "Выберите группу для удаления",
        reply_markup=reply_markup,
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
