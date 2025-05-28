import orjson
from aio_pika import IncomingMessage
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from src.data import settings
from src.enums import RabbitMQQueueConsumer
from src.keyboards.inline import user
from src.models.rabbitmq.client import ClientChatList
from src.rabbitmq import register_consumer


@register_consumer(RabbitMQQueueConsumer.CLIENT_ERROR)
async def handle_client_error(
    message: IncomingMessage,
    bot: Bot,
    dispatcher: Dispatcher,
) -> None:
    async with message.process():
        data = orjson.loads(message.body)
        user_id = data["user_id"]

        await bot.send_message(
            user_id,
            "Произошла ошибка при запуске клиента.",
        )


@register_consumer(RabbitMQQueueConsumer.CLIENT_STATUS)
async def handle_client_status(
    message: IncomingMessage,
    bot: Bot,
    dispatcher: Dispatcher,
) -> None:
    async with message.process():
        data = orjson.loads(message.body)
        user_id = data["user_id"]
        event = data["event"]

        if event == "disconnected":
            await bot.send_message(
                user_id,
                "Клиент отключен.",
            )
        elif event == "reconnected":
            await bot.send_message(
                user_id,
                "Клиент переподключен.",
            )
        elif event == "unauthorized":
            await bot.send_message(
                user_id,
                "Клиент не авторизован.",
            )


@register_consumer(RabbitMQQueueConsumer.CLIENT_STARTED)
async def handle_client_started(
    message: IncomingMessage,
    bot: Bot,
    dispatcher: Dispatcher,
) -> None:
    async with message.process():
        data = orjson.loads(message.body)
        user_id = data["user_id"]

        await bot.send_message(
            user_id,
            "Клиент успешно запущен.",
        )


@register_consumer(RabbitMQQueueConsumer.CLIENT_STOPPED)
async def handle_client_stopped(
    message: IncomingMessage,
    bot: Bot,
    dispatcher: Dispatcher,
) -> None:
    async with message.process():
        data = orjson.loads(message.body)
        user_id = data["user_id"]

        await bot.send_message(
            user_id,
            "Клиент успешно остановлен.",
        )


@register_consumer(RabbitMQQueueConsumer.CLIENT_CHAT_LIST)
async def handle_chat_get(
    message: IncomingMessage,
    bot: Bot,
    dispatcher: Dispatcher,
) -> None:
    async with message.process():
        data = orjson.loads(message.body)

        client_chat_list = ClientChatList(**data)

        state = FSMContext(
            storage=dispatcher.fsm.storage,
            key=StorageKey(
                bot_id=settings.bot.id,
                chat_id=client_chat_list.user_id,
                user_id=client_chat_list.user_id,
            ),
        )

        state_data = await state.get_data()
        working_message_id = state_data.get("working_message_id")
        await state.update_data(chats=[chat.model_dump() for chat in client_chat_list.chats])

        reply_markup = user.chat.ChatButtons().chats(
            chats=client_chat_list.chats,
            action="add",
            page=0,
        )
        await bot.edit_message_text(
            "Выберите группу для добавления",
            chat_id=client_chat_list.user_id,
            message_id=working_message_id,
            reply_markup=reply_markup,
        )
