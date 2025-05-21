import asyncio
from datetime import datetime

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.patched import Message

from src.db.repositories import ChatRepository
from src.infrastructure.rabbitmq.publisher import RabbitMQPublisher


class TelethonClientWrapper:
    def __init__(
        self,
        user_id: int,
        api_id: int,
        api_hash: str,
        session_string: str,
        publisher: RabbitMQPublisher,
        chat_repository: ChatRepository,
    ) -> None:
        self.user_id = user_id
        self.client = TelegramClient(StringSession(session_string), api_id, api_hash)
        self.publisher = publisher
        self.chat_repository = chat_repository
        self.background_tasks = set()
        self.allowed_chat_ids: set[int] = set()

    async def start(self) -> None:
        await self.client.connect()
        if not await self.client.is_user_authorized():
            raise Exception("Client not authorized")

        self.register_handlers()
        await self.update_chat_ids()

        task = asyncio.create_task(self.chat_updater_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    def register_handlers(self) -> None:
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

        await self.publisher.publish(
            queue_name="messages_to_process",
            message={
                "telegram_message_id": message_instance.id,
                "user_id": self.user_id,
                "chat_id": event.chat_id,
                "message_text": message_text,
                "sender_username": sender.username,
                "created_at": datetime.now(),
            },
        )

    async def chat_updater_loop(self) -> None:
        while True:
            await self.update_chat_ids()
            await asyncio.sleep(60)

    async def update_chat_ids(self) -> None:
        chats = await self.chat_repository.get_active_by_user_id(self.user_id)
        self.allowed_chat_ids = {chat.telegram_chat_id for chat in chats}

    async def stop(self) -> None:
        for task in self.background_tasks:
            task.cancel()
        await self.client.disconnect()

    async def send_message(
        self,
        entity_id: int,
        message: str,
        reply_to_message_id: int | None = None,
    ) -> None:
        entity = await self.client.get_entity(entity_id)
        await self.client.send_message(entity, message, reply_to=reply_to_message_id)
