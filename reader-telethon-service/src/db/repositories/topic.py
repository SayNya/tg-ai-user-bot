from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import Topic
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
