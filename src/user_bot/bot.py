from aiogram import Bot
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from src import utils
from src.data import config
from src.db.repositories.credentials import CredentialsRepository
from src.db.repositories.user import UserRepository
from src.models.chat import GroupModel


class UserClient:
    def __init__(
        self,
        user_id: int,
        context: utils.shared_context.AppContext,
        telegram_bot: Bot | None = None,
        client_bot: TelegramClient | None = None,
    ) -> None:
        self.user_id = user_id
        self.context = context
        self.client_bot = client_bot
        self.telegram_bot = telegram_bot

    async def init_client(self, api_id: int, api_hash: str, phone: str) -> str:
        self.client_bot = TelegramClient(
            session=config.SESSIONS_DIR / f"session_{self.user_id}.session",
            api_id=api_id,
            api_hash=api_hash,
        )
        await self.client_bot.connect()
        sent = await self.client_bot.send_code_request(phone=phone)

        return sent.phone_code_hash

    async def confirm_code(
        self,
        phone: str,
        code: str,
        phone_code_hash: str,
    ) -> None:
        if self.client_bot is None:
            return

        try:
            await self.client_bot.sign_in(
                phone=phone,
                code=code,
                phone_code_hash=phone_code_hash,
            )
        except SessionPasswordNeededError as e:
            raise SessionPasswordNeededError(e.request) from e

    async def enter_password(self, password: str) -> None:
        if self.client_bot is None:
            return
        await self.client_bot.sign_in(password=password)

    async def get_all_groups(self, limit: int) -> list[GroupModel]:
        if self.client_bot is None:
            return []
        groups = await self.client_bot.get_dialogs(limit=limit)
        return [
            GroupModel(id=group.id, name=group.title)
            for group in groups
            if group.is_group
        ]

    async def add_credentials(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
    ) -> None:
        cd_repository = CredentialsRepository(
            self.context["db_pool"],
            self.context["db_logger"],
        )
        await cd_repository.add_credentials(
            api_id=api_id,
            api_hash=api_hash,
            phone=phone,
            user_id=self.user_id,
        )
        cd_model = await cd_repository.get_credentials_by_user_id(self.user_id)
        if cd_model is None:
            return

        user_repository = UserRepository(
            self.context["db_pool"],
            self.context["db_logger"],
        )
        await user_repository.update_credentials(cd_model.id, self.user_id)
