import aio_pika
import orjson

from src.config import settings
from src.utils.logging import setup_logger

logger = setup_logger().bind(module="rabbitmq_publisher")


class RabbitMQPublisher:
    def __init__(self) -> None:
        self._channel = None
        logger.info("rabbitmq_publisher_initialized")

    async def connect(self) -> None:
        logger.info("connecting_to_rabbitmq")
        conn = await aio_pika.connect_robust(settings.rabbitmq.url)
        self._channel = await conn.channel()
        logger.info("rabbitmq_connected")

    async def publish(self, queue_name: str, message: dict) -> None:
        if self._channel is None:
            logger.info("channel_not_initialized_connecting")
            await self.connect()

        logger.info(
            "publishing_message",
            queue=queue_name,
            message_type=type(message).__name__,
        )

        await self._channel.default_exchange.publish(
            aio_pika.Message(body=orjson.dumps(message)),
            routing_key=queue_name,
        )
        logger.info("message_published", queue=queue_name)


publisher = RabbitMQPublisher()
