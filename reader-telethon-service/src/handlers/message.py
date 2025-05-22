from src.models.domain import MessageModel
from src.services import MessageService


class MessageHandlers:
    def __init__(self, message_service: MessageService) -> None:
        self.service = message_service

    async def handle_answer(self, payload: dict) -> None:
        model = MessageModel(**payload)

        await self.service.answer_message(model)
