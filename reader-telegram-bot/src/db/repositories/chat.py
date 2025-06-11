from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import Chat, ChatTopic
from src.models.database import ChatCreateDB, ChatDB

from .base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    schema_class = Chat

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(session_factory, logger)

    async def all(self) -> AsyncGenerator[ChatDB, None]:
        async for instance in self._all():
            yield ChatDB.model_validate(instance)

    async def get(self, id_: int) -> ChatDB:
        instance = await self._get(key="id", value=id_)
        return ChatDB.model_validate(instance)

    async def create(self, schema: ChatCreateDB) -> ChatDB:
        instance: Chat = await self._save(schema.model_dump())
        return ChatDB.model_validate(instance)

    async def get_by_telegram_chat_and_user(
        self,
        telegram_chat_id: int,
        user_id: int,
    ) -> ChatDB | None:
        query = select(Chat).where(
            Chat.telegram_chat_id == telegram_chat_id,
            Chat.user_id == user_id,
        )
        result = await self.execute(query)
        instance = result.scalar_one_or_none()
        return ChatDB.model_validate(instance) if instance else None

    async def reactivate(self, id_: int) -> ChatDB:
        instance = await self._update(key="id", value=id_, payload={"is_active": True})
        return ChatDB.model_validate(instance)

    async def get_active_chats_by_user_id(self, user_id: int) -> list[ChatDB]:
        stmt = select(Chat).where(
            Chat.user_id == user_id,
            Chat.is_active == True,
        )
        result = await self.execute(stmt)
        return [ChatDB.model_validate(instance) for instance in result.scalars().all()]

    async def deactivate(self, chat_id: int, user_id: int) -> ChatDB:
        async with self._session_factory() as session:
            query = (
                update(Chat)
                .where(
                    Chat.id == chat_id,
                    Chat.user_id == user_id,
                )
                .values(is_active=False)
                .returning(Chat)
            )
            result = await session.execute(query)
            await session.commit()
            instance = result.scalar_one()
            return ChatDB.model_validate(instance)

    async def get_chats_by_topic_id(self, topic_id: int) -> list[ChatDB]:
        stmt = select(Chat).join(ChatTopic).where(ChatTopic.topic_id == topic_id)
        result = await self.execute(stmt)
        return [ChatDB.model_validate(instance) for instance in result.scalars().all()]
