from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import User
from src.models.database import User as UserModel
from src.models.database import UserCreate

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    schema_class = User

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(session_factory, logger)

    async def all(self) -> AsyncGenerator[UserModel, None]:
        async for instance in self._all():
            yield UserModel.model_validate(instance)

    async def get(self, id_: int) -> UserModel:
        instance = await self._get(key="id", value=id_)
        return UserModel.model_validate(instance)

    async def create(self, schema: UserCreate) -> User:
        instance: User = await self._save(schema.model_dump())
        return UserModel.model_validate(instance)

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> UserModel | None:
        stmt = select(User).where(User.telegram_user_id == telegram_user_id)
        result = await self.execute(stmt)
        instance = result.scalars().first()
        return UserModel.model_validate(instance) if instance else None
