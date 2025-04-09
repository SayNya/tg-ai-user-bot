import asyncpg
import structlog

from src.db.db_api.storages import PostgresConnection
from src.models.theme import ThemeModel


class ThemeRepository(PostgresConnection):
    def __init__(
        self,
        connection_poll: asyncpg.Pool,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(connection_poll, logger)

    async def create_theme(
        self,
        name: str,
        description: str,
        gpt: str,
        user_id: int,
    ) -> None:
        statement = "INSERT INTO theme (name, description, gpt, user_id) VALUES ($1, $2, $3, $4);"
        await self._execute(
            sql=statement,
            params=(name, description, gpt, user_id),
        )

    async def get_themes_by_user_id(self, user_id: int) -> list[ThemeModel]:
        statement = "SELECT id, name, description, gpt FROM theme WHERE user_id = $1;"
        result = await self._fetch(
            sql=statement,
            params=(user_id,),
        )
        return result.convert(ThemeModel)

    async def get_themes_for_group(
        self,
        chat_id: int,
        user_id: int,
    ) -> list[ThemeModel]:
        statement = "SELECT t.* FROM theme t JOIN chat_theme tg ON t.id = tg.theme_id WHERE tg.chat_id = $1 AND tg.user_id = $2;"
        result = await self._fetch(
            statement,
            (chat_id, user_id),
        )
        return result.convert(ThemeModel)

    async def get_theme_by_name(self, user_id: int, name: str) -> ThemeModel:
        statement = "SELECT id, name, description, gpt FROM theme WHERE user_id = $1 AND name = $2;"
        result = await self._fetchrow(
            sql=statement,
            params=(user_id, name),
        )
        return result.convert(ThemeModel)

    async def get_theme_by_id(self, theme_id: int) -> ThemeModel | None:
        statement = "SELECT id, name, description, gpt FROM theme WHERE id = $1;"
        result = await self._fetchrow(
            sql=statement,
            params=(theme_id,),
        )
        return result.convert(ThemeModel)
