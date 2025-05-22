from aio_pika import IncomingMessage
from aiogram import Bot, Dispatcher
from src.enums import QueueName
from src.rabbitmq import register_consumer


@register_consumer(QueueName.TELEGRAM_STATUS)
async def handle_registration_status(
    message: IncomingMessage,
    bot: Bot,
    dispatcher: Dispatcher,
) -> None:
    async with message.process():
        pass
