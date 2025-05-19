from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core import settings


class DatabaseManager:
    def __init__(self):
        self.engine = create_async_engine(
            settings.database.url,
            echo=settings.debug,
            future=True,
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            yield session


db_manager = DatabaseManager()
