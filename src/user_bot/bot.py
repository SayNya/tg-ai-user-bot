import os

from telethon import TelegramClient

from src import utils
from src.data import config


async def setup_telethon_clients(context: utils.shared_context.AppContext) -> None:
    telethon_logger = context.get("telethon_logger")

    # Load saved sessions and initialize clients
    for session_file in os.listdir(config.SESSIONS_DIR):
        if session_file.endswith(".session"):
            user_id = session_file.split("_")[1].split(".")[0]
            session_path = config.SESSIONS_DIR / session_file
            client = TelegramClient(session_path, context.config.API_ID, context.config.API_HASH)

            await client.connect()
            client.run_until_disconnected()
            if await client.is_user_authorized():
                telethon_logger.info(f"Restored Telethon client for user {user_id}")
                context.set(f"telethon_client_{user_id}", client)
