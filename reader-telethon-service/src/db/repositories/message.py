from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import Message
from src.models.database import Message as MessageModel
from src.models.database import MessageCreate

from .base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    schema_class = Message

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(session_factory, logger)

    async def all(self) -> AsyncGenerator[MessageModel, None]:
        async for instance in self._all():
            yield MessageModel.model_validate(instance)

    async def get(self, id_: int) -> MessageModel:
        instance = await self._get(key="id", value=id_)
        return MessageModel.model_validate(instance)

    async def create(self, schema: MessageCreate) -> Message:
        instance: Message = await self._save(schema.model_dump())
        return MessageModel.model_validate(instance)
