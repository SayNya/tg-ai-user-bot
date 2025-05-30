from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import Message, Thread
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

    async def create(self, schema: MessageCreate) -> MessageModel:
        instance: Message = await self._save(schema.model_dump())
        return MessageModel.model_validate(instance)

    async def get_by_telegram_id(
        self,
        telegram_message_id: int,
        chat_id: int,
    ) -> MessageModel | None:
        stmt = (
            select(Message)
            .join(Thread, Message.thread_id == Thread.id)
            .where(
                Message.telegram_message_id == telegram_message_id,
                Thread.chat_id == chat_id,
            )
        )
        result = await self.execute(stmt)
        instance = result.scalar_one_or_none()
        return MessageModel.model_validate(instance) if instance else None

    async def get_thread_history(
        self,
        thread_id: int,
        limit: int = 7,
    ) -> list[MessageModel]:
        stmt = (
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.execute(stmt)
        return [
            MessageModel.model_validate(instance) for instance in result.scalars().all()
        ]
