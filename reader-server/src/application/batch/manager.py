from typing import Any, Callable

from src.domain import Message

from .collector import BatchCollector


class BatchCollectorManager:
    def __init__(
        self,
        batch_size: int,
        batch_time: int,
        process_func: Callable[[str, str, list[Message]], Any],
    ) -> None:
        self.batch_size = batch_size
        self.batch_time = batch_time
        self.process_func = process_func
        self.collectors: dict[tuple[str, str], BatchCollector] = {}

    async def add(self, msg: Message) -> None:
        key = (msg.user_id, msg.chat_id)
        if key not in self.collectors:
            self.collectors[key] = BatchCollector(
                self.batch_size,
                self.batch_time,
                lambda batch: self._on_batch(key, batch),
            )
        await self.collectors[key].add(msg)

    async def _on_batch(self, key: tuple[str, str], batch: list[Message]) -> None:
        user_id, chat_id = key
        await self.process_func(user_id, chat_id, batch)
        self.collectors.pop(key, None)
