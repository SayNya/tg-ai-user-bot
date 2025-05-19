import json

from aio_pika import DeliveryMode, Message, connect_robust

RABBITMQ_URL = "amqp://guest:guest@localhost/"


class RabbitMQPublisher:
    def __init__(self, url: str):
        self.url = url
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await connect_robust(self.url)
        self.channel = await self.connection.channel()

    async def send(self, queue_name: str, payload: dict):
        body = json.dumps(payload).encode()
        message = Message(body, delivery_mode=DeliveryMode.PERSISTENT)
        await self.channel.default_exchange.publish(message, routing_key=queue_name)

    async def close(self):
        if self.connection:
            await self.connection.close()


# Пример использования
async def send_telegram_init(api_id, api_hash, phone):
    publisher = RabbitMQPublisher()
    await publisher.connect()

    await publisher.send(
        "telegram.init",
        {
            "api_id": api_id,
            "api_hash": api_hash,
            "phone": phone,
        },
    )

    await publisher.close()
