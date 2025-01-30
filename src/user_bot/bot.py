from aiogram import Bot
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from src import utils
from src.data import config


class UserClient:
    def __init__(
        self,
        user_id: int,
        telegram_bot: Bot,
        context: utils.shared_context.AppContext,
    ) -> None:
        self.user_id = user_id
        self.telegram_bot = telegram_bot
        self.context = context
        self.client_bot: TelegramClient | None = None

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
