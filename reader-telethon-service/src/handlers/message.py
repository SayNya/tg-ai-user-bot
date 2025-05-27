import structlog

from src.models.domain import MessageModel
from src.services import MessageService


class MessageHandlers:
    def __init__(
        self,
        message_service: MessageService,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self.service = message_service
        self.logger = logger

    async def handle_answer(self, payload: dict) -> None:
        self.logger.info(
            "handle_answer_called",
            payload=payload,
            user_id=payload.get("user_id"),
        )
        try:
            model = MessageModel(**payload)
            await self.service.answer_message(model)
        except Exception as e:
            self.logger.exception(
                "handle_answer_error",
                user_id=payload.get("user_id"),
                error=str(e),
            )
            raise
