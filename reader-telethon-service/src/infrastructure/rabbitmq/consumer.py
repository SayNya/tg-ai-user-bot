from typing import Callable

import aio_pika
import orjson
import structlog


class RabbitMQConsumer:
    def __init__(
        self,
        connection_url: str,
        queue_handlers: dict[str, Callable],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self._connection_url = connection_url
        self._queue_handlers = queue_handlers
        self._connection = None
        self._channel = None
        self.logger = logger

    async def connect(self) -> None:
        self.logger.debug("rabbitmq_consumer_connecting", url=self._connection_url)
        self._connection = await aio_pika.connect_robust(self._connection_url)
        self._channel = await self._connection.channel()
        self.logger.debug("rabbitmq_consumer_connected", url=self._connection_url)

        for queue_name, handler in self._queue_handlers.items():
            self.logger.debug("rabbitmq_declaring_queue", queue=queue_name)
            queue = await self._channel.declare_queue(queue_name, durable=True)

            async def wrapper(msg, handler=handler):
                async with msg.process():
                    try:
                        payload = orjson.loads(msg.body)
                        self.logger.debug(
                            "rabbitmq_message_received",
                            queue=queue_name,
                            payload=payload,
                        )
                        await handler(payload)
                        self.logger.debug("rabbitmq_message_handled", queue=queue_name)
                    except Exception as e:
                        self.logger.exception(
                            "rabbitmq_message_error",
                            queue=queue_name,
                            error=str(e),
                        )
                        raise e

            await queue.consume(wrapper)
            self.logger.debug("rabbitmq_queue_consuming", queue=queue_name)

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            self.logger.debug(
                "rabbitmq_consumer_closing_connection",
                url=self._connection_url,
            )
            await self._connection.close()
            self.logger.debug(
                "rabbitmq_consumer_connection_closed",
                url=self._connection_url,
            )
