import orjson
from aio_pika import DeliveryMode, Message, RobustChannel
from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import Chat, User
from src.enums import RabbitMQQueuePublisher
from src.keyboards.inline import callbacks, user
from src.models.chat import ChatOut


async def chats_command(
    msg: types.Message,
    state: FSMContext,
) -> None:
    await state.clear()

    sent = await msg.answer(
        "Выберите действие:",
        reply_markup=user.group.GroupButtons().main(),
    )
    await state.update_data(working_message_id=sent.message_id)


async def choose_group_to_add(
    cb: types.CallbackQuery,
    callback_data: callbacks.GroupCallbackFactory,
    state: FSMContext,
    publisher_channel: RobustChannel,
    bot: Bot,
) -> None:
    data = await state.get_data()
    chats = data.get("chats")
    if chats is None:
        payload = {
            "user_id": cb.from_user.id,
        }
        body = orjson.dumps(payload)
        message = Message(body, delivery_mode=DeliveryMode.PERSISTENT)
        await publisher_channel.default_exchange.publish(
            message,
            routing_key=RabbitMQQueuePublisher.CLIENT_CHAT_LIST,
        )

        data = await state.get_data()
        working_message_id = data.get("working_message_id")
        await bot.edit_message_text(
            "Подождите, идёт обработка",
            chat_id=cb.message.chat.id,
            message_id=working_message_id,
        )
        return

    page = callback_data.page
    reply_markup = user.group.GroupButtons().groups(chats, "add", page)
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
    chats = data.get("chats", [])

    chat_name = None
    for chat in chats:
        if chat.id == callback_data.id:
            chat_name = chat.name
            break

    if not chat_name:
        await cb.message.answer("Ошибка: информация о группе не найдена.")
        return

    stmt = (
        insert(Chat)
        .values(
            telegram_chat_id=callback_data.id,
            title=chat_name,
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


async def choose_chat_to_delete(
    cb: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    page: int = 0,
) -> None:
    # Fetch groups only once
    data = await state.get_data()
    chats = data.get("active_chats")
    if chats is None:
        stmt = select(User).where(
            User.telegram_user_id == cb.from_user.id,
        )
        res = await session.execute(stmt)
        user = res.scalars().one_or_none()
        stmt = select(Chat).where(
            Chat.user_id == user.id,
            Chat.is_active == True,
        )
        res = await session.execute(stmt)
        chats = [ChatOut(**chat) for chat in res.scalars().all()]
        await state.update_data(active_chats=chats)

    # Display paginated groups
    reply_markup = user.group.GroupButtons().groups(chats, "delete", page)
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
