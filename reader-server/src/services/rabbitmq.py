import aio_pika
from src.config import settings


class RabbitMQClient:
    def __init__(self) -> None:
        self.connection = None
        self.channel = None

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self.channel = await self.connection.channel()

    async def publish(self, routing_key: str, message_body: bytes) -> None:
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=message_body),
            routing_key=routing_key,
        )

    async def close(self) -> None:
        if self.connection:
            await self.connection.close()


rabbitmq_client = RabbitMQClient()
