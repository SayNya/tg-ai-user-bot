from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import TelegramAuth
from src.models.database import TelegramAuthCreateDB, TelegramAuthDB

from .base import BaseRepository


class TelegramAuthRepository(BaseRepository[TelegramAuth]):
    schema_class = TelegramAuth

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(session_factory, logger)

    async def all(self) -> AsyncGenerator[TelegramAuthDB, None]:
        async for instance in self._all():
            yield TelegramAuthDB.model_validate(instance)

    async def get(self, id_: int) -> TelegramAuthDB:
        instance = await self._get(key="id", value=id_)
        return TelegramAuthDB.model_validate(instance)

    async def create(self, schema: TelegramAuthCreateDB) -> TelegramAuthDB:
        instance = await self._save(schema.model_dump())
        return TelegramAuthDB.model_validate(instance)
