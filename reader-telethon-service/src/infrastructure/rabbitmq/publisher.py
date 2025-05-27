import aio_pika
import orjson
import structlog


class RabbitMQPublisher:
    def __init__(
        self,
        connection_url: str,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self._connection_url = connection_url
        self._connection = None
        self._channel = None
        self.logger = logger

    async def connect(self) -> None:
        if self._connection is None or self._connection.is_closed:
            self.logger.debug("rabbitmq_connecting", url=self._connection_url)
            self._connection = await aio_pika.connect_robust(self._connection_url)
            self._channel = await self._connection.channel()
            self.logger.debug("rabbitmq_connected", url=self._connection_url)

    async def publish(self, routing_key: str, message: dict) -> None:
        await self.connect()
        self.logger.debug(
            "rabbitmq_publish_attempt",
            routing_key=routing_key,
            message=message,
        )
        try:
            await self._channel.default_exchange.publish(
                aio_pika.Message(body=orjson.dumps(message)),
                routing_key=routing_key,
            )
            self.logger.debug("rabbitmq_publish_success", routing_key=routing_key)
        except Exception as e:
            self.logger.exception(
                "rabbitmq_publish_error",
                routing_key=routing_key,
                error=str(e),
            )
            raise e

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            self.logger.debug("rabbitmq_closing_connection", url=self._connection_url)
            await self._connection.close()
            self.logger.debug("rabbitmq_connection_closed", url=self._connection_url)
