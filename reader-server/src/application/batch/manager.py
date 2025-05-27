from typing import Any, Callable

import structlog

from src.domain import Message

from .collector import BatchCollector
from .processor import BatchProcessor


class BatchManager:
    def __init__(
        self,
        batch_size: int,
        batch_time: int,
        process_func: Callable[[list[Message]], Any],
        logger: structlog.typing.FilteringBoundLogger,
    ):
        self.collector = BatchCollector(
            batch_size,
            batch_time,
            self._process_batch,
            logger,
        )
        self.processor = BatchProcessor(process_func, logger)
        self.logger = logger

    async def add(self, msg: Message) -> None:
        self.logger.debug(
            "adding_message_to_batch",
            message_id=msg.id,
        )
        await self.collector.add(msg)

    async def _process_batch(self, messages: list[Message]) -> None:
        self.logger.info(
            "processing_batch",
            batch_size=len(messages),
        )
        try:
            await self.processor.process(messages)
            self.logger.info(
                "batch_processed_successfully",
                batch_size=len(messages),
            )
        except Exception as e:
            self.logger.exception(
                "batch_processing_failed",
                batch_size=len(messages),
                error=str(e),
            )
            raise
