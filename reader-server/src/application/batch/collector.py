import asyncio
from typing import Any, Callable

from src.domain import Message


class BatchCollector:
    def __init__(
        self,
        batch_size: int,
        batch_time: int,
        process_func: Callable[[list[Message]], Any],
    ):
        self.batch_size = batch_size
        self.batch_time = batch_time
        self.process_func = process_func
        self.buffer: list[Message] = []
        self.lock = asyncio.Lock()
        self.timer_task: asyncio.Task | None = None

    async def add(self, msg: Message) -> None:
        async with self.lock:
            if not self.buffer:
                self.timer_task = asyncio.create_task(self._flush_by_time())
            self.buffer.append(msg)
            if len(self.buffer) >= self.batch_size:
                await self._flush()

    async def _flush(self) -> None:
        if self.buffer:
            to_process = self.buffer.copy()
            self.buffer.clear()
            if self.timer_task:
                self.timer_task.cancel()
                self.timer_task = None
            await self.process_func(to_process)

    async def _flush_by_time(self) -> None:
        try:
            await asyncio.sleep(self.batch_time)
            async with self.lock:
                await self._flush()
        except asyncio.CancelledError:
            pass
