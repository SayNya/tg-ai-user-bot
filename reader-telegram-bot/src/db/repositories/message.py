from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import Message
from src.models.database import MessageCreateDB, MessageDB

from .base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    schema_class = Message

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(session_factory, logger)

    async def all(self) -> AsyncGenerator[MessageDB, None]:
        async for instance in self._all():
            yield MessageDB.model_validate(instance)

    async def get(self, id_: int) -> MessageDB:
        instance = await self._get(key="id", value=id_)
        return MessageDB.model_validate(instance)

    async def create(self, schema: MessageCreateDB) -> MessageDB:
        instance: Message = await self._save(schema.model_dump())
        return MessageDB.model_validate(instance)
