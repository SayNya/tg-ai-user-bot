from aiogram import Bot
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from src import utils
from src.data import config
from src.db.repositories import ChatRepository, ThemeRepository
from src.db.repositories.credentials import CredentialsRepository
from src.db.repositories.message import MessageRepository
from src.db.repositories.user import UserRepository
from src.models import MessageModel
from src.models.chat import GroupModel
from src.models.theme import ThemeModel


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

        self.theme_repository = ThemeRepository(
            self.context["db_pool"], self.context["db_logger"]
        )
        self.chat_repository = ChatRepository(
            self.context["db_pool"], self.context["db_logger"]
        )
        self.credentials_repository = CredentialsRepository(
            self.context["db_pool"], self.context["db_logger"]
        )
        self.user_repository = UserRepository(
            self.context["db_pool"], self.context["db_logger"]
        )
        self.message_repository = MessageRepository(
            self.context["db_pool"], self.context["db_logger"]
        )

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

    async def get_active_group_ids(self) -> list[int]:
        groups = await self.chat_repository.get_active_groups_for_user(self.user_id)
        return [group.id for group in groups]

    async def get_active_groups(self) -> list[GroupModel]:
        groups = await self.chat_repository.get_active_groups_for_user(self.user_id)
        return groups

    async def get_themes(self) -> list[ThemeModel]:
        themes = await self.theme_repository.get_themes_by_user_id(self.user_id)
        return themes

    async def get_theme_by_name(self, name: str) -> ThemeModel:
        theme = await self.theme_repository.get_theme_by_name(self.user_id, name)
        return theme

    async def get_theme_by_id(self, theme_id: int) -> ThemeModel:
        theme = await self.theme_repository.get_theme_by_id(theme_id)
        return theme

    async def add_credentials(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
    ) -> None:
        await self.credentials_repository.add_credentials(
            api_id=api_id,
            api_hash=api_hash,
            phone=phone,
            user_id=self.user_id,
        )
        cd_model = await self.credentials_repository.get_credentials_by_user_id(
            self.user_id
        )
        if cd_model is None:
            return

        await self.user_repository.update_credentials(cd_model.id, self.user_id)

    async def add_message(
        self,
        msg_id: int,
        text: str,
        chat_id: int,
        sender_id: int,
        theme_id: int,
        mentioned_id: int | None = None,
    ) -> None:
        await self.message_repository.create_message(
            msg_id=msg_id,
            text=text,
            chat_id=chat_id,
            mentioned_id=mentioned_id,
            user_id=self.user_id,
            sender_id=sender_id,
            theme_id=theme_id,
        )

    async def get_mentioned_message(
        self,
        chat_id: int,
        msg_id: int,
        sender_id: int,
    ) -> MessageModel | None:
        return await self.message_repository.get_mentioned_message(
            msg_id=msg_id, chat_id=chat_id, user_id=self.user_id, sender_id=sender_id
        )

    async def get_messages_tree(
        self,
        msg_id: int,
    ) -> list[MessageModel] | None:
        return await self.message_repository.get_messages_tree(
            message_id=msg_id,
        )

    async def get_private_chat_history(
        self,
        chat_id: int,
    ) -> list[MessageModel] | None:
        return await self.message_repository.get_private_chat_history(
            chat_id=chat_id,
            user_id=self.user_id,
        )
