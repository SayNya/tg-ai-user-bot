import asyncio
import logging
from datetime import datetime

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.patched import Message

from src.db.repositories import get_user_chat_tg_ids_from_db
from src.rabbitmq import publisher


async def handle_event_buffer(
    user_id: int,
    event: events.newmessage.NewMessage.Event,
) -> None:
    message_instance: Message = event.message
    message_text: str = message_instance.message
    sender = await event.get_sender()

    await publisher.publish(
        queue_name="messages_to_process",
        message={
            "telegram_message_id": message_instance.id,
            "user_id": user_id,
            "chat_id": event.chat_id,
            "message_text": message_text,
            "sender_username": sender.username,
            "created_at": datetime.now(),
        },
    )


class ClientWrapper:
    def __init__(
        self,
        user_id: int,
        session_string: str,
        api_id: int,
        api_hash: str,
    ) -> None:
        self.user_id = user_id
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string
        self.client = TelegramClient(StringSession(session_string), api_id, api_hash)
        self.allowed_chat_ids: set[int] = set()
        self.started = False

    async def start(self) -> None:
        if self.started:
            return
        await self.client.start()
        await self.update_chat_ids()

        @self.client.on(events.NewMessage(func=lambda e: e.is_group))
        async def handler(event) -> None:
            if event.chat_id in self.allowed_chat_ids:
                await handle_event_buffer(self.user_id, event)

        asyncio.create_task(self.chat_updater_loop())
        asyncio.create_task(self.monitor_disconnect())
        self.started = True

    async def chat_updater_loop(self) -> None:
        while True:
            try:
                await self.update_chat_ids()
            except Exception as e:
                logging.warning(f"Failed to update chat ids for {self.user_id}: {e}")
            await asyncio.sleep(60)

    async def update_chat_ids(self) -> None:
        chat_ids = await get_user_chat_tg_ids_from_db(self.user_id)
        self.allowed_chat_ids = set(chat_ids)

    async def monitor_disconnect(self) -> None:
        try:
            await self.client.run_until_disconnected()
        except Exception as e:
            logging.exception(f"Client {self.user_id} disconnected unexpectedly: {e}")
            await asyncio.sleep(5)
            await self.start()  # перезапуск клиента


class ClientManager:
    def __init__(self) -> None:
        self.clients: dict[int, ClientWrapper] = {}

    async def start_client(
        self,
        user_id: int,
        session_string: str,
        api_id: int,
        api_hash: str,
    ) -> None:
        if user_id in self.clients:
            logging.info(f"Client {user_id} already running")
            return
        wrapper = ClientWrapper(user_id, session_string, api_id, api_hash)
        self.clients[user_id] = wrapper
        await wrapper.start()

    def get_wrapper(self, user_id: int) -> ClientWrapper | None:
        return self.clients.get(user_id)
