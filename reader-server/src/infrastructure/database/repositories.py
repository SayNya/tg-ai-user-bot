from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain import Topic as DomainTopic

from .models import Chat as DBChat
from .models import ChatTopic as DBChatTopic
from .models import Topic as DBTopic


class SQLAlchemyTopicRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_topic(self, topic: DomainTopic) -> DomainTopic:
        db_topic = DBTopic(
            topic_id=topic.topic_id,
            name=topic.name,
            description=topic.description,
        )
        self.session.add(db_topic)
        await self.session.commit()
        await self.session.refresh(db_topic)
        return DomainTopic(
            topic_id=db_topic.topic_id,
            name=db_topic.name,
            description=db_topic.description,
        )

    async def get_topic(self, topic_id: str) -> DomainTopic | None:
        result = await self.session.execute(
            select(DBTopic).where(DBTopic.topic_id == topic_id),
        )
        db_topic = result.scalar_one_or_none()
        if db_topic:
            return DomainTopic(
                topic_id=db_topic.topic_id,
                name=db_topic.name,
                description=db_topic.description,
            )
        return None

    async def get_chat_topics(
        self,
        user_id: str,
        chat_id: str,
    ) -> list[DomainTopic] | None:
        result = await self.session.execute(
            select(DBTopic)
            .join(DBChatTopic, DBTopic.id == DBChatTopic.topic_id)
            .join(DBChat, DBChat.id == DBChatTopic.chat_id)
            .where(DBChat.telegram_chat_id == chat_id)
            .where(DBChat.user_id == user_id),
        )
        return [
            DomainTopic(
                id=topic.id,
                name=topic.name,
                description=topic.description,
                prompt=topic.prompt,
            )
            for topic in result.scalars().all()
        ]

    async def update_topic(self, topic: DomainTopic) -> DomainTopic:
        db_topic = await self.session.get(DBTopic, topic.topic_id)
        if db_topic:
            db_topic.name = topic.name
            db_topic.description = topic.description
            await self.session.commit()
            await self.session.refresh(db_topic)
            return DomainTopic(
                topic_id=db_topic.topic_id,
                name=db_topic.name,
                description=db_topic.description,
            )
        return topic

    async def delete_topic(self, topic_id: str) -> bool:
        db_topic = await self.session.get(DBTopic, topic_id)
        if db_topic:
            await self.session.delete(db_topic)
            await self.session.commit()
            return True
        return False


class SQLAlchemyMessageRepository:
    pass
