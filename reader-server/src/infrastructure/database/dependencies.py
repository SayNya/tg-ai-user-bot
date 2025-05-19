from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from .connection import db_manager
from .repositories import (
    SQLAlchemyMessageRepository,
    SQLAlchemyTopicRepository,
)


@asynccontextmanager
async def get_topic_repository() -> AsyncIterator[SQLAlchemyTopicRepository]:
    async for session in db_manager.get_session():
        yield SQLAlchemyTopicRepository(session)
        break


@asynccontextmanager
async def get_message_repository() -> AsyncIterator[SQLAlchemyMessageRepository]:
    async for session in db_manager.get_session():
        yield SQLAlchemyMessageRepository(session)
        break
