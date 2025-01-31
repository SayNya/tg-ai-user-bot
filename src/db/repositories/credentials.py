import asyncpg
import structlog

from src.db.db_api.storages import PostgresConnection
from src.models.credentials import CredentialsModel


class CredentialsRepository(PostgresConnection):
    def __init__(
        self,
        connection_poll: asyncpg.Pool,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(connection_poll, logger)

    async def add_credentials(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
        user_id: int,
    ) -> None:
        statement = "INSERT INTO credentials (api_id, api_hash, phone, user_id) VALUES ($1, $2, $3, $4);"
        await self._execute(statement, (api_id, api_hash, phone, user_id))

    async def get_credentials_by_user_id(self, user_id: int) -> CredentialsModel | None:
        statement = "SELECT id, api_id, api_hash, phone, user_id FROM credentials WHERE user_id = $1;"
        result = await self._fetchrow(sql=statement, params=(user_id,))
        return result.convert(CredentialsModel)
