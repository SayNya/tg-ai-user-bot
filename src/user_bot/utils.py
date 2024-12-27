import asyncpg
from pyrogram import Client
from pyrogram.enums import ChatType

from src.db.repositories import ChatRepository, ThemeRepository
from src.models import GroupModel
from src.models.chat import CHAT_TYPE_MAPPING
from src.models.theme import ThemeModel


class UserBot:
    def __init__(self, client: Client, db_pool: asyncpg.Pool, db_logger):
        self.client = client
        self.db_pool = db_pool
        self.db_logger = db_logger
        self.active_groups = []

    async def get_all_groups(self, limit: int = 0) -> list[GroupModel]:
        return [
            GroupModel(
                id=dialog.chat.id,
                name=dialog.chat.title,
                type=CHAT_TYPE_MAPPING[dialog.chat.type],
            )
            async for dialog in self.client.get_dialogs(limit=limit)
            if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        ]

    async def get_active_groups(self) -> list[GroupModel]:
        chat_repository = ChatRepository(self.db_pool, self.db_logger)
        groups = await chat_repository.get_active_groups_for_user(
            self.client.me.id,
            [ChatType.GROUP, ChatType.SUPERGROUP],
        )
        return groups

    async def get_themes(self) -> list[ThemeModel]:
        theme_repository = ThemeRepository(self.db_pool, self.db_logger)
        groups = await theme_repository.get_themes_by_user_id(
            self.client.me.id,
        )
        return groups
