import asyncio
import re

import structlog
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.patched import Message

from src.db.repositories import (
    ChatRepository,
    MessageRepository,
    ThreadRepository,
    TopicRepository,
)
from src.infrastructure import RabbitMQPublisher
from src.models.domain import ChatModel
from src.models.enums.infrastructure import RabbitMQQueuePublisher


class TelethonClientWrapper:
    def __init__(
        self,
        user_id: int,
        api_id: int,
        api_hash: str,
        session_string: str,
        publisher: RabbitMQPublisher,
        chat_repository: ChatRepository,
        message_repository: MessageRepository,
        thread_repository: ThreadRepository,
        topic_repository: TopicRepository,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self.user_id = user_id
        self.client = TelegramClient(StringSession(session_string), api_id, api_hash)
        self.publisher = publisher
        self.chat_repository = chat_repository
        self.message_repository = message_repository
        self.thread_repository = thread_repository
        self.topic_repository = topic_repository
        self.background_tasks = set()
        self.allowed_chat_ids: set[int] = set()
        self.logger = logger

    async def start(self) -> None:
        self.logger.info("starting_client", user_id=self.user_id)
        await self.client.connect()
        if not await self.client.is_user_authorized():
            self.logger.error("client_unauthorized", user_id=self.user_id)
            await self.publisher.publish(
                RabbitMQQueuePublisher.CLIENT_STATUS,
                {"user_id": self.user_id, "event": "unauthorized"},
            )
            return

        self.register_handlers()
        await self.update_chat_ids()
        self.logger.info("client_started", user_id=self.user_id)

        task = asyncio.create_task(self.chat_updater_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    def register_handlers(self) -> None:
        self.logger.debug("registering_message_handlers", user_id=self.user_id)

        @self.client.on(events.NewMessage)
        async def handler(event: events.newmessage.NewMessage.Event) -> None:
            if event.chat_id in self.allowed_chat_ids:
                await self.handle_event_buffer(event)

    async def handle_event_buffer(
        self,
        event: events.newmessage.NewMessage.Event,
    ) -> None:
        message_instance: Message = event.message
        sender = await event.get_sender()

        self.logger.debug(
            "processing_message",
            user_id=self.user_id,
            chat_id=event.chat_id,
            message_id=message_instance.id,
            sender_username=sender.username,
        )
        reply_to_msg_id = message_instance.reply_to_msg_id
        thread_id = await self.find_existing_thread_id(
            chat_id=event.chat_id,
            sender_id=sender.id,
            reply_to_msg_id=reply_to_msg_id,
        )

        if thread_id:
            # await self.publisher.publish(
            #     RabbitMQQueuePublisher.MESSAGE_PROCESS_THREAD,
            #     message={
            #         "telegram_message_id": message_instance.id,
            #         "user_id": self.user_id,
            #         "chat_id": event.chat_id,
            #         "text": message_instance.message,
            #         "sender_username": sender.username,
            #         "sender_id": sender.id,
            #         "thread_id": thread_id,
            #         "reply_to_msg_id": reply_to_msg_id,
            #         "created_at": message_instance.date,
            #     },
            # )
            pass
        else:
            topics = await self.topic_repository.get_by_chat_id()
            message_text = message_instance.message.lower()

            # Remove punctuation and split into words
            message_words = set(re.findall(r"\w+", message_text))

            # Check each topic's keywords
            for topic in topics:
                if not topic.keywords:
                    continue

                # Count how many keywords match
                matching_keywords = 0
                for keyword in topic.keywords:
                    # Remove punctuation from keyword and convert to lowercase
                    clean_keyword = re.findall(r"\w+", keyword.lower())[0]
                    # Check if keyword is part of any word in the message
                    if any(clean_keyword in word for word in message_words):
                        matching_keywords += 1

                # If more than 2 keywords match, process the message
                if matching_keywords > 0:
                    await self.publisher.publish(
                        RabbitMQQueuePublisher.MESSAGE_PROCESS,
                        message={
                            "telegram_message_id": message_instance.id,
                            "user_id": self.user_id,
                            "chat_id": event.chat_id,
                            "text": message_instance.message,
                            "sender_username": sender.username,
                            "sender_id": sender.id,
                            "created_at": message_instance.date,
                            "topic_id": topic.id,
                            "score": float(matching_keywords),
                        },
                    )
                    break

    async def find_existing_thread_id(
        self,
        chat_id: int,
        sender_id: int,
        reply_to_msg_id: int | None,
    ) -> int | None:
        # 1. Try to find the message being replied to
        if reply_to_msg_id:
            chat = await self.chat_repository.get_by_telegram_chat_id(chat_id)
            message = await self.message_repository.get_by_telegram_id(
                reply_to_msg_id,
                chat.id,
            )
            if message and message.thread_id:
                # Update thread activity since we're continuing the conversation
                await self.thread_repository.update_activity(message.thread_id)
                return message.thread_id
            return None

        # 2. Try to find an active thread with the same initiator
        # active_threshold = (datetime.now(UTC) - timedelta(seconds=5)).replace(
        #     tzinfo=None,
        # )
        # active_thread = await self.thread_repository.get_active_thread(
        #     chat_id=chat_id,
        #     initiator_id=sender_id,
        #     active_threshold=active_threshold,
        # )
        # if active_thread:
        #     await self.thread_repository.update_activity(active_thread.id)
        #     return active_thread.id
        return None

    async def chat_updater_loop(self) -> None:
        self.logger.debug("starting_chat_updater_loop", user_id=self.user_id)
        while True:
            try:
                await self.update_chat_ids()
                await asyncio.sleep(60)
            except Exception as e:
                self.logger.exception(
                    "chat_updater_loop_error",
                    user_id=self.user_id,
                    error=str(e),
                )

    async def update_chat_ids(self) -> None:
        self.logger.debug("updating_chat_ids", user_id=self.user_id)
        chats = await self.chat_repository.get_active_by_user_id(self.user_id)
        self.allowed_chat_ids = {chat.telegram_chat_id for chat in chats}
        self.logger.debug(
            "chat_ids_updated",
            user_id=self.user_id,
            chat_count=len(self.allowed_chat_ids),
        )

    async def stop(self) -> None:
        self.logger.info("stopping_client", user_id=self.user_id)
        for task in self.background_tasks:
            task.cancel()
        await self.client.disconnect()
        self.logger.info("client_stopped", user_id=self.user_id)

    async def send_message(
        self,
        entity_id: int,
        message: str,
        reply_to_message_id: int | None = None,
    ) -> Message:
        self.logger.debug(
            "sending_message",
            user_id=self.user_id,
            entity_id=entity_id,
            reply_to=reply_to_message_id,
        )
        try:
            entity = await self.client.get_entity(entity_id)
            sent_message = await self.client.send_message(
                entity,
                message,
                reply_to=reply_to_message_id,
            )
            self.logger.debug(
                "message_sent",
                user_id=self.user_id,
                entity_id=entity_id,
                message_id=sent_message.id,
            )
            return sent_message
        except Exception as e:
            self.logger.exception(
                "failed_to_send_message",
                user_id=self.user_id,
                entity_id=entity_id,
                error=str(e),
            )
            raise

    async def get_chat_list(self) -> list[ChatModel]:
        dialogs = await self.client.get_dialogs(limit=100)
        return [
            ChatModel(id=dialog.id, name=dialog.name)
            for dialog in dialogs
            if dialog.is_group
        ][:30]
