import asyncpg
import structlog

from src.db.db_api.storages import PostgresConnection


class MessageRepository(PostgresConnection):
    def __init__(
        self,
        connection_poll: asyncpg.Pool,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(connection_poll, logger)
