import asyncpg
import structlog

from src.db.db_api.storages import PostgresConnection
from src.models.user import UserModel


class UserRepository(PostgresConnection):
    def __init__(
        self,
        connection_poll: asyncpg.Pool,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(connection_poll, logger)

    async def create_user(
        self,
        user_id: int,
        is_bot: bool,
        first_name: str,
        last_name: str | None,
        username: str | None,
        language_code: str | None,
    ) -> None:
        statement = "INSERT INTO public.user (id, is_bot, first_name, last_name, username, language_code) VALUES ($1, $2, $3, $4, $5, $6);"
        await self._execute(
            sql=statement,
            params=(user_id, is_bot, first_name, last_name, username, language_code),
        )

    async def get_user_by_id(self, user_id: int) -> UserModel | None:
        statement = "SELECT id FROM public.user WHERE id = $1"
        result = await self._fetchrow(sql=statement, params=(user_id,))

        if not result:
            return None

        return result.convert(UserModel)

    async def update_credentials(
        self,
        credentials_id: int,
        user_id: int,
    ) -> None:
        statement = "UPDATE public.user SET credentials_id = $1 WHERE id = $2;"
        await self._execute(statement, (credentials_id, user_id))
