import orjson
from aio_pika import DeliveryMode, Message, RobustChannel
from aiogram import Bot, types
from aiogram.fsm.context import FSMContext

from src.db.repositories import ChatRepository
from src.enums import RabbitMQQueuePublisher
from src.keyboards.inline import callbacks, user
from src.models.database import ChatCreateDB
from src.models.rabbitmq import Chat


async def chats_command(
    msg: types.Message,
    state: FSMContext,
) -> None:
    await state.clear()

    sent = await msg.answer(
        "Выберите действие:",
        reply_markup=user.chat.ChatButtons().main(),
    )
    await state.update_data(working_message_id=sent.message_id)


async def choose_chat_to_add(
    cb: types.CallbackQuery,
    callback_data: callbacks.ChatCallbackFactory,
    state: FSMContext,
    publisher_channel: RobustChannel,
    bot: Bot,
) -> None:
    data = await state.get_data()
    chats = [Chat(**chat) for chat in data.get("chats", [])]

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

    reply_markup = user.chat.ChatButtons().chats(
        chats=chats,
        action="add",
        page=page,
    )
    await cb.message.edit_text(
        "Выберите группу для добавления",
        reply_markup=reply_markup,
    )
    await cb.answer()


async def add_chat(
    cb: types.CallbackQuery,
    callback_data: callbacks.ChangeChatCallbackFactory,
    state: FSMContext,
    chat_repository: ChatRepository,
) -> None:
    data = await state.get_data()
    chats = [Chat(**chat) for chat in data.get("chats", [])]

    chat_rabbitmq = None
    for chat in chats:
        if chat.id == callback_data.id:
            chat_rabbitmq = chat
            break

    if not chat_rabbitmq:
        await cb.message.answer("Ошибка: информация о группе не найдена.")
        return

    existing_chat = await chat_repository.get_by_telegram_chat_and_user(
        telegram_chat_id=chat_rabbitmq.id,
        user_id=cb.from_user.id,
    )

    if existing_chat:
        await chat_repository.reactivate(existing_chat.id)
        await cb.message.answer("Группа успешно реактивирована")
    else:
        chat_create = ChatCreateDB(
            telegram_chat_id=chat_rabbitmq.id,
            title=chat_rabbitmq.name,
            user_id=cb.from_user.id,
        )
        await chat_repository.create(chat_create)
        await cb.message.answer("Группа успешно добавлена в обработку")

    await cb.message.delete()


async def choose_chat_to_delete(
    cb: types.CallbackQuery,
    state: FSMContext,
    chat_repository: ChatRepository,
    page: int = 0,
) -> None:
    data = await state.get_data()
    chats = [Chat(**chat) for chat in data.get("active_chats", [])]
    if chats is None:
        chats = await chat_repository.get_active_chats_by_user_id(cb.from_user.id)
        await state.update_data(active_chats=[chat.model_dump() for chat in chats])

    reply_markup = user.chat.ChatButtons().chats(chats, "delete", page)
    await cb.message.edit_text(
        "Выберите группу для удаления",
        reply_markup=reply_markup,
    )
    await cb.answer()


async def delete_chat(
    cb: types.CallbackQuery,
    callback_data: callbacks.ChangeChatCallbackFactory,
    chat_repository: ChatRepository,
) -> None:
    await chat_repository.deactivate(
        telegram_chat_id=callback_data.id,
        user_id=cb.from_user.id,
    )
    await cb.message.answer("Группа успешно удалена из обработки")
