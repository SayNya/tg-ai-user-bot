from typing import Callable

import aio_pika
import orjson


class RabbitMQConsumer:
    def __init__(
        self,
        connection_url: str,
        queue_handlers: dict[str, Callable],
    ) -> None:
        self._connection_url = connection_url
        self._queue_handlers = queue_handlers
        self._connection = None
        self._channel = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._connection_url)
        self._channel = await self._connection.channel()

        for queue_name, handler in self._queue_handlers.items():
            queue = await self._channel.declare_queue(queue_name, durable=True)

            async def wrapper(msg, handler=handler):
                async with msg.process():
                    try:
                        payload = orjson.loads(msg.body)
                        await handler(payload)
                    except Exception:
                        pass

            await queue.consume(wrapper)

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
