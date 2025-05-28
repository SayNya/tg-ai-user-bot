import asyncio
from datetime import datetime, timezone

import structlog
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.patched import Message

from src.db.repositories import ChatRepository
from src.infrastructure.rabbitmq.publisher import RabbitMQPublisher
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
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self.user_id = user_id
        self.client = TelegramClient(StringSession(session_string), api_id, api_hash)
        self.publisher = publisher
        self.chat_repository = chat_repository
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
        message_text: str = message_instance.message
        sender = await event.get_sender()

        self.logger.debug(
            "processing_message",
            user_id=self.user_id,
            chat_id=event.chat_id,
            message_id=message_instance.id,
            sender_username=sender.username,
        )

        await self.publisher.publish(
            RabbitMQQueuePublisher.MESSAGE_PROCESS,
            message={
                "telegram_message_id": message_instance.id,
                "user_id": self.user_id,
                "chat_id": event.chat_id,
                "message_text": message_text,
                "sender_username": sender.username,
                "created_at": datetime.now(timezone.utc),
            },
        )

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
        return [ChatModel(id=dialog.id, name=dialog.name) for dialog in dialogs if dialog.is_group][:30]
