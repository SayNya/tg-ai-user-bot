from aiogram import types
from aiogram.fsm.context import FSMContext
from sqlalchemy import insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import Chat
from src.keyboards.inline import callbacks, user


async def chats_command(
    msg: types.Message,
    state: FSMContext,
) -> None:
    await state.clear()
    m = "Выберите действие:"
    await msg.answer(m, reply_markup=user.group.GroupButtons().main())


async def choose_group_to_add(
    cb: types.CallbackQuery,
    callback_data: callbacks.GroupCallbackFactory,
    state: FSMContext,
) -> None:
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
    state: FSMContext,
    session: AsyncSession,
) -> None:
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

    stmt = (
        insert(Chat)
        .values(
            telegram_chat_id=callback_data.id,
            title=group_name,
            user_id=cb.from_user.id,
            is_active=True,
        )
        .on_conflict_do_update(
            constraint=["uix_chat_user"],
            set_={"is_active": True},
        )
    )

    await session.execute(stmt)
    await session.commit()

    await cb.message.answer("Группа успешно добавлена в обработку")
    await cb.message.delete()


async def choose_group_to_delete(
    cb: types.CallbackQuery,
    state: FSMContext,
    page: int = 0,
) -> None:
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
    session: AsyncSession,
) -> None:
    stmt = (
        update(Chat)
        .where(
            Chat.telegram_chat_id == callback_data.id,
            Chat.user_id == cb.from_user.id,
        )
        .values(is_active=False)
    )
    await session.execute(stmt)
    await session.commit()

    await cb.message.answer("Группа успешно удалена из обработки")
