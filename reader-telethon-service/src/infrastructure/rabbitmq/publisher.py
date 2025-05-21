import aio_pika
import orjson


class RabbitMQPublisher:
    def __init__(self, connection_url: str) -> None:
        self._connection_url = connection_url
        self._connection = None
        self._channel = None

    async def connect(self) -> None:
        if self._connection is None or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(self._connection_url)
            self._channel = await self._connection.channel()

    async def publish(self, routing_key: str, message: dict) -> None:
        await self.connect()
        try:
            await self._channel.default_exchange.publish(
                aio_pika.Message(body=orjson.dumps(message)),
                routing_key=routing_key,
            )
        except Exception as e:
            raise e

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
