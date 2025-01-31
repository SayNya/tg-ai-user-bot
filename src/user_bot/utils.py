from pathlib import Path

from telethon import TelegramClient

from src import utils
from src.data import config
from src.db.repositories.credentials import CredentialsRepository
from src.models.credentials import CredentialsModel
from src.user_bot.bot import UserClient


async def setup_telethon_clients(context: utils.shared_context.AppContext) -> None:
    # aiogram_logger = logging.getLogger("aiogram")
    # aiogram_logger.propagate = False

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

    await user_bot.client_bot.start(phone=credentials.phone)  # type: ignore
