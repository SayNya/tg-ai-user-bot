from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import Chat, ChatTopic, Thread, Topic
from src.models.database import Topic as TopicModel
from src.models.database import TopicCreate

from .base import BaseRepository


class TopicRepository(BaseRepository[Topic]):
    schema_class = Topic

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(session_factory, logger)

    async def all(self) -> AsyncGenerator[TopicModel, None]:
        async for instance in self._all():
            yield TopicModel.model_validate(instance)

    async def get(self, id_: int) -> TopicModel:
        instance = await self._get(key="id", value=id_)
        return TopicModel.model_validate(instance)

    async def create(self, schema: TopicCreate) -> TopicModel:
        instance = await self._save(schema.model_dump())
        return TopicModel.model_validate(instance)

    async def get_by_thread_id(self, thread_id: int) -> TopicModel:
        stmt = (
            select(Topic)
            .join(Thread, Thread.topic_id == Topic.id)
            .where(Thread.id == thread_id)
        )
        result = await self.execute(stmt)
        instance = result.scalar_one_or_none()
        return TopicModel.model_validate(instance)

    async def get_by_chat_id(self, chat_id: int, user_id: int) -> list[TopicModel]:
        stmt = (
            select(Topic)
            .join(ChatTopic, Topic.id == ChatTopic.topic_id)
            .join(Chat, Chat.id == ChatTopic.chat_id)
            .where(Chat.telegram_chat_id == chat_id)
            .where(Chat.user_id == user_id),
        )
        result = await self.execute(stmt)
        return [
            TopicModel.model_validate(instance) for instance in result.scalars.all()
        ]
