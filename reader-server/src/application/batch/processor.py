from typing import Any, Callable

import structlog

from src.domain import Message


class BatchProcessor:
    def __init__(
        self,
        process_func: Callable[[list[Message]], Any],
        logger: structlog.typing.FilteringBoundLogger,
    ):
        self.process_func = process_func
        self.logger = logger

    async def process(self, messages: list[Message]) -> None:
        if not messages:
            self.logger.debug("no_messages_to_process")
            return

        self.logger.info(
            "starting_batch_processing",
            batch_size=len(messages),
        )
        try:
            await self.process_func(messages)
            self.logger.info(
                "batch_processing_completed",
                batch_size=len(messages),
            )
        except Exception as e:
            self.logger.exception(
                "batch_processing_failed",
                batch_size=len(messages),
                error=str(e),
            )
            raise
