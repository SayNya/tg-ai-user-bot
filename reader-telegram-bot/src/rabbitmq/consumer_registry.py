from collections.abc import Awaitable
from typing import Callable

from aio_pika import IncomingMessage

ConsumerHandler = Callable[[IncomingMessage], Awaitable[None]]

registry: dict[str, ConsumerHandler] = {}


def register_consumer(queue_name: str):
    def decorator(func: ConsumerHandler):
        registry[queue_name] = func
        return func

    return decorator
