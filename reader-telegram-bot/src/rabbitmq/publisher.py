import orjson
from aio_pika import DeliveryMode, Message, RobustChannel

from src.enums import RabbitMQQueuePublisher


class RabbitMQPublisher:
    def __init__(self, channel: RobustChannel) -> None:
        self.channel = channel

    async def publish(
        self,
        payload: dict,
        routing_key: RabbitMQQueuePublisher,
    ) -> None:
        """Publish message to RabbitMQ queue.

        Args:
            payload: Dictionary with message data
            routing_key: Queue routing key from RabbitMQQueuePublisher enum
        """
        body = orjson.dumps(payload)
        message = Message(body, delivery_mode=DeliveryMode.PERSISTENT)
        await self.channel.default_exchange.publish(
            message,
            routing_key=routing_key,
        )
