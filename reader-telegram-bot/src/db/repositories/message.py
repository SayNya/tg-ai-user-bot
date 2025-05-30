import datetime
from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from src.db.tables import Chat, Message, Thread
from src.models.database import DettailedMessageDB, MessageCreateDB, MessageDB

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

    async def get_with_details(
        self,
        user_id: int,
        created_at: datetime,
    ) -> list[DettailedMessageDB]:
        stmt = (
            select(Message)
            .join(Message.thread)
            .join(Thread.chat)
            .where(Chat.user_id == user_id)
            .where(Message.created_at > created_at)
            .options(
                selectinload(Message.thread).options(
                    selectinload(Thread.chat),
                    selectinload(Thread.topic),
                ),
            )
        )
        result = await self.execute(stmt)
        instances = result.scalars().all()
        return [DettailedMessageDB.model_validate(inst) for inst in instances]
