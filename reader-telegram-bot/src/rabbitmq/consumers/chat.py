import orjson
from aio_pika import IncomingMessage
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from src.data import settings
from src.enums import RabbitMQQueueConsumer
from src.keyboards.inline import user
from src.models import ChatTest
from src.rabbitmq import register_consumer


@register_consumer(RabbitMQQueueConsumer.CLIENT_CHAT_LIST)
async def handle_chat_get(
    message: IncomingMessage,
    bot: Bot,
    dispatcher: Dispatcher,
) -> None:
    async with message.process():
        data = orjson.loads(message.body)
        user_id = data["user_id"]
        chats = [ChatTest(**chat) for chat in data["chats"]]

        state = FSMContext(
            storage=dispatcher.fsm.storage,
            key=StorageKey(bot_id=settings.bot.id, chat_id=user_id, user_id=user_id),
        )

        state_data = await state.get_data()
        working_message_id = state_data.get("working_message_id")
        await state.update_data(chats=chats)
        reply_markup = user.group.GroupButtons().groups(chats, "add", 1)
        await bot.edit_message_text(
            "Выберите группу для добавления",
            chat_id=user_id,
            message_id=working_message_id,
            reply_markup=reply_markup,
        )
