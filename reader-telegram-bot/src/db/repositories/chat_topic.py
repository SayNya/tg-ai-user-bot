from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import Chat
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
    
    