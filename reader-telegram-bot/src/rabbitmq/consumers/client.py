import orjson
from aio_pika import IncomingMessage
from aiogram import Bot, Dispatcher
from src.enums import RabbitMQQueueConsumer
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
