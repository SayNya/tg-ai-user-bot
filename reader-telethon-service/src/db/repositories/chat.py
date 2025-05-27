from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import Chat
from src.models.database import Chat as ChatModel
from src.models.database import ChatCreate

from .base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    schema_class = Chat

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(session_factory, logger)

    async def all(self) -> AsyncGenerator[ChatModel, None]:
        async for instance in self._all():
            yield ChatModel.model_validate(instance)

    async def get(self, id_: int) -> ChatModel:
        instance = await self._get(key="id", value=id_)
        return ChatModel.model_validate(instance)

    async def create(self, schema: ChatCreate) -> Chat:
        instance: Chat = await self._save(schema.model_dump())
        return ChatModel.model_validate(instance)

    async def get_active_by_user_id(self, user_id: int) -> list[ChatModel] | None:
        stmt = select(Chat).where(Chat.user_id == user_id, Chat.is_active == True)
        result = await self.execute(stmt)
        instance = result.scalars().all()
        return [ChatModel.model_validate(instance) for instance in instance]
