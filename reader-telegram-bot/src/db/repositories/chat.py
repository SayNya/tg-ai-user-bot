import asyncpg
import structlog

from src.db.db_api.storages import PostgresConnection
from src.models import GroupModel


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
    ) -> list[GroupModel]:
        statement = "SELECT id, name FROM chat WHERE user_id = $1 AND active = $2;"
        result = await self._fetch(
            statement,
            (user_id, True),
        )
        return result.convert(GroupModel)

    async def add_chat(
        self,
        chat_id: int,
        chat_name: str,
        user_id: int,
    ) -> None:
        statement = "INSERT INTO chat (id, name, user_id) VALUES ($1, $2, $3);"
        await self._execute(statement, (chat_id, chat_name, user_id))

    async def deactivate_chat(self, chat_id: int, user_id: int) -> None:
        statement = "UPDATE chat SET active = $1 WHERE id = $2 AND user_id = $3;"
        await self._execute(statement, (False, chat_id, user_id))

    async def activate_chat(self, chat_id: int, user_id: int) -> None:
        statement = "UPDATE chat SET active = $1 WHERE id = $2 AND user_id = $3;"
        await self._execute(statement, (True, chat_id, user_id))

    async def get_group_by_id(self, chat_id: int, user_id: int) -> GroupModel:
        statement = "SELECT id, name FROM chat WHERE user_id = $1 AND id = $2;"
        result = await self._fetchrow(
            statement,
            (user_id, chat_id),
        )
        return result.convert(GroupModel)
