import structlog
from openai import AsyncOpenAI

from src.db.repositories import ChatRepository, MessageRepository, TopicRepository
from src.infrastructure import TelethonClientManager
from src.models.database import MessageCreate
from src.models.domain import MessageModel
from src.models.enums import SenderType


class MessageService:
    def __init__(
        self,
        client_manager: TelethonClientManager,
        topic_repository: TopicRepository,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
        openai_client: AsyncOpenAI,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self.client_manager = client_manager
        self.topic_repository = topic_repository
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.openai_client = openai_client
        self.logger = logger

    async def answer_message(self, message_model: MessageModel) -> None:
        self.logger.info(
            "processing_message",
            user_id=message_model.user_id,
            chat_id=message_model.chat_id,
            topic_id=message_model.topic_id,
        )
        chat = await self.chat_repository.get_by_telegram_chat_id(message_model.chat_id)
        message_user = MessageCreate(
            telegram_message_id=message_model.telegram_message_id,
            sender_type=SenderType.USER,
            sender_username=message_model.sender_username,
            content=message_model.content,
            chat_id=chat.id,
            topic_id=message_model.topic_id,
        )
        await self.message_repository.create(message_user)

        topic = await self.topic_repository.get(message_model.topic_id)
        self.logger.debug("retrieved_topic", topic_id=topic.id)

        prompt = f"Сообщение пользователя:\n{message_model.content}"
        self.logger.debug("generating_response", prompt=prompt)

        answer_data = await self.ask_openai(prompt, topic.prompt)
        self.logger.debug(
            "openai_response",
            prompt_tokens=answer_data["prompt_tokens"],
            completion_tokens=answer_data["completion_tokens"],
        )

        client = self.client_manager.get_client(message_model.user_id)
        if not client:
            self.logger.error(
                "client_not_found",
                user_id=message_model.user_id,
            )
            return

        sent_msg = await client.send_message(
            message_model.chat_id,
            answer_data["content"],
            reply_to=message_model.telegram_message_id,
        )

        message_bot = MessageCreate(
            telegram_message_id=sent_msg.id,
            sender_type=SenderType.BOT,
            content=answer_data["content"],
            chat_id=chat.id,
            confidence_score=message_model.score,
            prompt_tokens=answer_data["prompt_tokens"],
            completion_tokens=answer_data["completion_tokens"],
            topic_id=message_model.topic_id,
        )
        await self.message_repository.create(message_bot)
        self.logger.info(
            "message_answered",
            user_id=message_model.user_id,
            chat_id=message_model.chat_id,
            message_id=sent_msg.id,
        )

    async def ask_openai(self, prompt: str, system_prompt: str) -> dict:
        self.logger.debug(
            "calling_openai",
            prompt_length=len(prompt),
            system_prompt_length=len(system_prompt),
        )
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            return {
                "content": response.choices[0].message.content,
                "total_tokens": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }
        except Exception as e:
            self.logger.error(
                "openai_error",
                error=str(e),
                prompt_length=len(prompt),
            )
            raise
