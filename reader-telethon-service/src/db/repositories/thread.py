from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import Chat, Thread
from src.models.database import Thread as ThreadModel
from src.models.database import ThreadCreate

from .base import BaseRepository


class ThreadRepository(BaseRepository[Thread]):
    schema_class = Thread

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(session_factory, logger)

    async def all(self) -> AsyncGenerator[ThreadModel, None]:
        async for instance in self._all():
            yield ThreadModel.model_validate(instance)

    async def get(self, id_: int) -> ThreadModel:
        instance = await self._get(key="id", value=id_)
        return ThreadModel.model_validate(instance)

    async def create(self, schema: ThreadCreate) -> ThreadModel:
        instance: Thread = await self._save(schema.model_dump())
        return ThreadModel.model_validate(instance)

    async def get_active_thread(
        self,
        chat_id: int,
        initiator_id: int,
        active_threshold: datetime,
    ) -> ThreadModel | None:
        stmt = (
            select(Thread)
            .join(Chat, Thread.chat_id == Chat.id)
            .where(
                Chat.telegram_chat_id == chat_id,
                Thread.initiator_id == initiator_id,
                Thread.last_activity_at >= active_threshold,
            )
            .order_by(Thread.last_activity_at.asc())
        )
        result = await self.execute(stmt)
        instance = result.scalars().first()
        return ThreadModel.model_validate(instance) if instance else None

    async def update_activity(self, thread_id: int) -> ThreadModel:
        thread = await self._update(
            key="id",
            value=thread_id,
            payload={"last_activity_at": datetime.now(UTC).replace(tzinfo=None)},
        )

        return ThreadModel.model_validate(thread)
