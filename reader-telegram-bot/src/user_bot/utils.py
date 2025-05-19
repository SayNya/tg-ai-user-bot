import logging
from functools import partial
from pathlib import Path

from telethon import TelegramClient, events

from src.context import AppContext
from src.data import settings
from src.db.repositories.credentials import CredentialsRepository
from src.models.credentials import CredentialsModel
from src.user_bot.bot import UserClient
from src.user_bot.handlers import chat_handler, private_handler


async def setup_telethon_clients(context: AppContext) -> None:
    aiogram_logger = logging.getLogger("telethon")
    aiogram_logger.propagate = False

    cd_repository = CredentialsRepository(
        context.get("db_pool"),
        context.get("db_logger"),
    )
    for session_file in settings.sessions_dir.iterdir():
        session_file_str = str(session_file)
        if session_file_str.endswith(".session"):
            user_id = int(session_file_str.split("_")[-1].split(".")[0])
            session_path = settings.sessions_dir / session_file_str
            credentials_model = await cd_repository.get_credentials_by_user_id(user_id)
            if credentials_model is None:
                continue
            await __start_client(credentials_model, session_path, context)


async def __start_client(
    credentials: CredentialsModel,
    session_path: Path,
    context: AppContext,
) -> None:
    if credentials.user_id is None:
        return

    client = TelegramClient(
        session_path,
        api_id=credentials.api_id,
        api_hash=credentials.api_hash,
    )
    await client.connect()
    if not await client.is_user_authorized():
        await notify_user_about_reauth(credentials.user_id, context)
        return

    user_bot = UserClient(credentials.user_id, context, client_bot=client)
    client.add_event_handler(
        partial(chat_handler, user_client=user_bot),
        events.NewMessage(func=lambda e: e.is_group),
    )

    client.add_event_handler(
        partial(private_handler, user_client=user_bot),
        events.NewMessage(func=lambda e: e.is_private),
    )

    await client.start(phone=credentials.phone)

    context["user_clients"][credentials.user_id] = user_bot
    context["telethon_logger"].info(
        f"Restored Telethon client for user {credentials.user_id}",
    )


async def notify_user_about_reauth(user_id: int, context: AppContext) -> None:
    telegram_bot = context["telegram_bot"]
    await telegram_bot.send_message(
        chat_id=user_id,
        text=(
            "⚠️ Ваша сессия Telegram была отключена. "
            "Пожалуйста, восстановите сессию, используя команду /restore_session."
        ),
    )
