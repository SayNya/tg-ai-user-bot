import structlog

from src.models.domain import MessageFromLLM, MessageFromTelethon
from src.services import MessageService


class MessageHandlers:
    def __init__(
        self,
        message_service: MessageService,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self.service = message_service
        self.logger = logger

    async def handle_llm_answer(self, payload: dict) -> None:
        self.logger.info(
            "handle_answer_called",
            payload=payload,
            user_id=payload.get("user_id"),
        )
        try:
            model = MessageFromLLM(**payload)
            await self.service.process_msg_without_thread(model)
        except Exception as e:
            self.logger.exception(
                "handle_answer_error",
                user_id=payload.get("user_id"),
                error=str(e),
            )
            raise

    async def handle_telethon_answer(self, payload: dict) -> None:
        self.logger.info(
            "handle_elethon_answer_called",
            payload=payload,
            user_id=payload.get("user_id"),
        )
        try:
            model = MessageFromTelethon(**payload)
            await self.service.process_msg_with_thread(model)
        except Exception as e:
            self.logger.exception(
                "handle_elethon_answer_error",
                user_id=payload.get("user_id"),
                error=str(e),
            )
            raise
