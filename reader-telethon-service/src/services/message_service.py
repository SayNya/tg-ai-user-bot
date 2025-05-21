import openai

from src.db.repositories import TopicRepository
from src.infrastructure import TelethonClientManager
from src.models.domain import MessageModel


class MessageService:
    def __init__(
        self,
        client_manager: TelethonClientManager,
        topic_repository: TopicRepository,
    ) -> None:
        self.client_manager = client_manager
        self.topic_repository = topic_repository

    async def answer_message(self, message_model: MessageModel) -> None:
        topic = await self.topic_repository.get(message_model.topic_id)

        prompt = f"{topic.prompt}\n\nСообщение пользователя:\n{message_model.content}"

        answer = await self.ask_openai(prompt)

        client = self.client_manager.get_client(message_model.user_id)
        if not client:
            return

        await client.send_message(
            message_model.chat_id,
            answer,
            reply_to=message_model.telegram_message_id,
        )

    @staticmethod
    async def ask_openai(prompt: str) -> str:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
