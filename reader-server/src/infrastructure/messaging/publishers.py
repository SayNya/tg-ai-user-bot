import json

import aio_pika

from src.core import settings
from src.domain import AnswerTask


class AnswerTaskPublisher:
    def __init__(self, rabbitmq_url: str = settings.rabbitmq.url):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.queue = None

    async def connect(self):
        if not self.connection:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            self.queue = await self.channel.declare_queue(
                settings.ANSWER_QUEUE_NAME,
                durable=True,
            )

    async def send(self, task: AnswerTask) -> None:
        if not self.channel:
            await self.connect()

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=task.model_dump_json().encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=settings.ANSWER_QUEUE_NAME,
        )
