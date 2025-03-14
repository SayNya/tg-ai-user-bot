import logging
from functools import partial
from pathlib import Path

from telethon import TelegramClient, events

from src import utils
from src.data import config
from src.db.repositories.credentials import CredentialsRepository
from src.models.credentials import CredentialsModel
from src.user_bot.bot import UserClient
from src.user_bot.handlers import message_handler


async def setup_telethon_clients(context: utils.shared_context.AppContext) -> None:
    aiogram_logger = logging.getLogger("telethon")
    aiogram_logger.propagate = False

    cd_repository = CredentialsRepository(
        context.get("db_pool"),
        context.get("db_logger"),
    )
    for session_file in config.SESSIONS_DIR.iterdir():
        session_file_str = str(session_file)
        if session_file_str.endswith(".session"):
            user_id = int(session_file_str.split("_")[-1].split(".")[0])
            session_path = config.SESSIONS_DIR / session_file_str
            credentials_model = await cd_repository.get_credentials_by_user_id(user_id)
            if credentials_model is None:
                continue
            await __start_client(credentials_model, session_path, context)


async def __start_client(
    credentials: CredentialsModel,
    session_path: Path,
    context: utils.shared_context.AppContext,
) -> None:
    if credentials.user_id is None:
        return

    client = TelegramClient(
        session_path,
        api_id=credentials.api_id,
        api_hash=credentials.api_hash,
    )

    user_bot = UserClient(credentials.user_id, context, client_bot=client)

    client.add_event_handler(partial(message_handler, user_client=user_bot), events.NewMessage)

    await user_bot.client_bot.start(phone=credentials.phone)  # type: ignore
    context["user_clients"][credentials.user_id] = user_bot
    context["telethon_logger"].info(
        f"Restored Telethon client for user {credentials.user_id}",
    )
