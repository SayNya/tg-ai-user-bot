import asyncpg
import structlog

from src.db.db_api.storages import PostgresConnection
from src.models import CHAT_TYPE_MAPPING, GroupModel


class ChatRepository(PostgresConnection):
    def __init__(
        self,
        connection_poll: asyncpg.Pool,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(connection_poll, logger)

    async def get_active_groups_for_user(
        self,
        user_id: int,
        chat_types,
    ) -> list[GroupModel]:
        statement = "SELECT id, name, type FROM chat WHERE user_id = $1 AND type = ANY($2) AND active = $3;"
        result = await self._fetch(
            statement,
            (user_id, [CHAT_TYPE_MAPPING[chat_type] for chat_type in chat_types], True),
        )
        return result.convert(GroupModel)

    async def add_chat(
        self,
        chat_id: int,
        chat_type: str,
        chat_name: str,
        user_id: int,
    ) -> None:
        statement = (
            "INSERT INTO chat (id, type, name, user_id) VALUES ($1, $2, $3, $4);"
        )
        await self._execute(statement, (chat_id, chat_type, chat_name, user_id))

    async def deactivate_chat(self, chat_id: int, user_id: int) -> None:
        statement = "UPDATE chat SET active = $1 WHERE id = $2 AND user_id = $3;"
        await self._execute(statement, (False, chat_id, user_id))
