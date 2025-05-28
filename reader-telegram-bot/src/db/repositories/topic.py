from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import ChatTopic, Topic
from src.models.database import TopicCreateDB, TopicDB

from .base import BaseRepository


class TopicRepository(BaseRepository[Topic]):
    schema_class = Topic

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(session_factory, logger)

    async def all(self) -> AsyncGenerator[TopicDB, None]:
        async for instance in self._all():
            yield TopicDB.model_validate(instance)

    async def get(self, id_: int) -> TopicDB:
        instance = await self._get(key="id", value=id_)
        return TopicDB.model_validate(instance)

    async def create(self, schema: TopicCreateDB) -> TopicDB:
        instance = await self._save(schema.model_dump())
        return TopicDB.model_validate(instance)

    async def get_all_by_user_id(self, user_id: int) -> list[TopicDB]:
        stmt = select(Topic).where(Topic.user_id == user_id)
        result = await self.execute(stmt)
        return [TopicDB.model_validate(instance) for instance in result.scalars().all()]

    async def get_all_by_user_id_and_chat_id(
        self, user_id: int, chat_id: int,
    ) -> list[TopicDB]:
        stmt = (
            select(Topic)
            .join(ChatTopic, Topic.id == ChatTopic.topic_id)
            .where(
                ChatTopic.chat_id == chat_id,
                ChatTopic.user_id == user_id,
            )
        )
        result = await self.execute(stmt)
        return [TopicDB.model_validate(instance) for instance in result.scalars().all()]

    async def update_name(self, id_: int, name: str) -> TopicDB:
        instance = await self._update(key="id", value=id_, payload={"name": name})
        return TopicDB.model_validate(instance)

    async def update_description(self, id_: int, description: str) -> TopicDB:
        instance = await self._update(
            key="id",
            value=id_,
            payload={"description": description},
        )
        return TopicDB.model_validate(instance)

    async def update_prompt(self, id_: int, prompt: str) -> TopicDB:
        instance = await self._update(key="id", value=id_, payload={"prompt": prompt})
        return TopicDB.model_validate(instance)
