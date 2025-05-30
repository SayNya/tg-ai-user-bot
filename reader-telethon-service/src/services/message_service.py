from typing import Union

import structlog
from openai import AsyncOpenAI

from src.db.repositories import (
    ChatRepository,
    MessageRepository,
    ThreadRepository,
    TopicRepository,
)
from src.infrastructure import TelethonClientManager
from src.models.database import MessageCreate, Thread, ThreadCreate
from src.models.domain import MessageFromLLM, MessageFromTelethon
from src.models.enums import SenderType


class MessageService:
    def __init__(
        self,
        client_manager: TelethonClientManager,
        topic_repository: TopicRepository,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
        thread_repository: ThreadRepository,
        openai_client: AsyncOpenAI,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self.client_manager = client_manager
        self.topic_repository = topic_repository
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.thread_repository = thread_repository
        self.openai_client = openai_client
        self.logger = logger

    async def process_msg_without_thread(self, message_model: MessageFromLLM) -> None:
        self.logger.info(
            "processing_message",
            user_id=message_model.user_id,
            chat_id=message_model.chat_id,
            topic_id=message_model.topic_id,
        )

        thread = await self._create_thread(message_model)
        reply_id = await self._create_user_message(message_model, thread.id)

        topic = await self.topic_repository.get(message_model.topic_id)
        self.logger.debug("retrieved_topic", topic_id=topic.id)

        messages = [
            {"role": "system", "content": topic.prompt},
            {"role": "user", "content": message_model.text},
        ]

        answer_data = await self._get_openai_response(messages)
        await self._send_and_save_bot_response(
            message_model,
            answer_data,
            thread.id,
            reply_id,
        )

    async def process_msg_with_thread(self, message_model: MessageFromTelethon) -> None:
        """Process a message within an existing thread."""
        self.logger.info(
            "processing_message_with_thread",
            user_id=message_model.user_id,
            chat_id=message_model.chat_id,
            thread_id=message_model.thread_id,
        )

        reply_id = await self._create_user_message(
            message_model,
            message_model.thread_id,
        )
        self.logger.debug("created_user_message", reply_id=reply_id)

        topic = await self.topic_repository.get_by_thread_id(message_model.thread_id)
        self.logger.debug("retrieved_topic", topic_id=topic.id)

        message_history = await self._get_formatted_message_history(
            message_model.thread_id,
        )
        self.logger.debug(
            "retrieved_message_history",
            thread_id=message_model.thread_id,
            message_count=len(message_history),
        )

        messages = [{"role": "system", "content": topic.prompt}] + message_history
        answer_data = await self._get_openai_response(messages)

        await self._send_and_save_bot_response(
            message_model,
            answer_data,
            message_model.thread_id,
            reply_id,
        )
        self.logger.info(
            "completed_message_processing",
            thread_id=message_model.thread_id,
            user_id=message_model.user_id,
        )

    async def _create_thread(self, message_model: MessageFromLLM) -> Thread:
        chat = await self.chat_repository.get_by_telegram_chat_id(message_model.chat_id)
        thread_create = ThreadCreate(
            initiator_id=message_model.sender_id,
            initiator_username=message_model.sender_username,
            chat_id=chat.id,
            topic_id=message_model.topic_id,
            confidence_score=message_model.score,
            last_activity_at=message_model.created_at.replace(tzinfo=None),
        )
        return await self.thread_repository.create(thread_create)

    async def _create_user_message(
        self,
        message_model: Union[MessageFromLLM, MessageFromTelethon],
        thread_id: int,
        parent_message_id: int | None = None,
    ) -> int:
        message_user = MessageCreate(
            telegram_message_id=message_model.telegram_message_id,
            sender_type=SenderType.USER,
            content=message_model.text,
            thread_id=thread_id,
            parent_message_id=parent_message_id,
        )
        message = await self.message_repository.create(message_user)
        return message.id

    async def _get_formatted_message_history(
        self,
        thread_id: int,
    ) -> list[dict[str, str]]:
        message_history = await self.message_repository.get_thread_history(
            thread_id=thread_id,
        )
        return [
            {
                "role": "user" if msg.sender_type == SenderType.USER else "assistant",
                "content": msg.content,
            }
            for msg in reversed(message_history)
        ]

    async def _send_and_save_bot_response(
        self,
        message_model: Union[MessageFromLLM, MessageFromTelethon],
        answer_data: dict[str, str | int],
        thread_id: int,
        reply_id: int,
    ) -> None:
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
            reply_to_message_id=message_model.telegram_message_id,
        )

        message_bot = MessageCreate(
            telegram_message_id=sent_msg.id,
            sender_type=SenderType.BOT,
            content=answer_data["content"],
            prompt_tokens=answer_data["prompt_tokens"],
            completion_tokens=answer_data["completion_tokens"],
            parent_message_id=reply_id,
            thread_id=thread_id,
        )
        await self.message_repository.create(message_bot)
        self.logger.info(
            "message_answered",
            user_id=message_model.user_id,
            chat_id=message_model.chat_id,
            message_id=sent_msg.id,
        )

    async def _get_openai_response(
        self,
        messages: list[dict[str, str]],
    ) -> dict[str, str | int]:
        self.logger.debug("generating_response", messages=messages)
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
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
                message_count=len(messages),
            )
            raise
