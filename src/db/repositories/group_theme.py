import asyncpg
import structlog

from src.db.db_api.storages import PostgresConnection


class GroupThemeRepository(PostgresConnection):
    def __init__(
        self,
        connection_poll: asyncpg.Pool,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(connection_poll, logger)

    async def add_group_theme(self, chat_id: int, theme_id: int, user_id: int) -> None:
        statement = (
            "INSERT INTO chat_theme (chat_id, theme_id, user_id) VALUES ($1, $2, $3);"
        )
        await self._execute(statement, (chat_id, theme_id, user_id))

    async def remove_group_theme(self, chat_id: int, theme_id: int, user_id: int) -> None:
        statement = (
            "DELETE FROM chat_theme WHERE chat_id = $1 AND theme_id = $2 AND user_id = $3;"
        )
        await self._execute(statement, (chat_id, theme_id, user_id))

    # async def deactivate_chat(self, chat_id: int, user_id: int) -> None:
    #     statement = "UPDATE chat SET active = $1 WHERE id = $2 AND user_id = $3;"
    #     await self._execute(statement, (False, chat_id, user_id))
