import asyncio
from typing import Any, Callable

import structlog

from src.domain import Message


class BatchCollector:
    def __init__(
        self,
        batch_size: int,
        batch_time: int,
        process_func: Callable[[list[Message]], Any],
        logger: structlog.typing.FilteringBoundLogger,
    ):
        self.batch_size = batch_size
        self.batch_time = batch_time
        self.process_func = process_func
        self.buffer: list[Message] = []
        self.lock = asyncio.Lock()
        self.timer_task: asyncio.Task | None = None
        self.logger = logger

    async def add(self, msg: Message) -> None:
        async with self.lock:
            if not self.buffer:
                self.logger.debug(
                    "starting_batch_timer",
                    batch_time=self.batch_time,
                )
                self.timer_task = asyncio.create_task(self._flush_by_time())
            self.buffer.append(msg)
            self.logger.debug(
                "message_added_to_batch",
                buffer_size=len(self.buffer),
                batch_size=self.batch_size,
            )
            if len(self.buffer) >= self.batch_size:
                await self._flush()

    async def _flush(self) -> None:
        if self.buffer:
            to_process = self.buffer.copy()
            self.buffer.clear()
            if self.timer_task:
                self.timer_task.cancel()
                self.timer_task = None
            self.logger.info(
                "flushing_batch",
                batch_size=len(to_process),
            )
            try:
                await self.process_func(to_process)
                self.logger.info(
                    "batch_processed_successfully",
                    batch_size=len(to_process),
                )
            except Exception as e:
                self.logger.exception(
                    "batch_processing_error",
                    batch_size=len(to_process),
                    error=str(e),
                )
                raise

    async def _flush_by_time(self) -> None:
        try:
            await asyncio.sleep(self.batch_time)
            async with self.lock:
                await self._flush()
        except asyncio.CancelledError:
            self.logger.debug("batch_timer_cancelled")
