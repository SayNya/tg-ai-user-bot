import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import ChatTopic

from .base import BaseRepository


class ChatTopicRepository(BaseRepository[ChatTopic]):
    schema_class = ChatTopic

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(session_factory, logger)

    async def get_bound_topics(self, chat_id: int) -> list[int]:
        """Get list of topic IDs bound to a chat."""
        stmt = select(ChatTopic.topic_id).where(ChatTopic.chat_id == chat_id)
        result = await self.execute(stmt)
        return [row[0] for row in result.all()]

    async def bind_topics(self, chat_id: int, topic_ids: list[int]) -> None:
        """Bind multiple topics to a chat."""
        async with self._session_factory() as session:
            for topic_id in topic_ids:
                chat_topic = ChatTopic(chat_id=chat_id, topic_id=topic_id)
                session.add(chat_topic)
            await session.commit()

    async def unbind_topics(self, chat_id: int, topic_ids: list[int]) -> None:
        """Unbind multiple topics from a chat."""
        async with self._session_factory() as session:
            stmt = delete(ChatTopic).where(
                ChatTopic.chat_id == chat_id,
                ChatTopic.topic_id.in_(topic_ids),
            )
            await session.execute(stmt)
            await session.commit()
