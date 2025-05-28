from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import User
from src.models.database import UserCreateDB, UserDB

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    schema_class = User

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(session_factory, logger)

    async def all(self) -> AsyncGenerator[UserDB, None]:
        async for instance in self._all():
            yield UserDB.model_validate(instance)

    async def get(self, id_: int) -> UserDB:
        instance = await self._get(key="id", value=id_)
        return UserDB.model_validate(instance)

    async def create(self, schema: UserCreateDB) -> UserDB:
        instance: User = await self._save(schema.model_dump())
        return UserDB.model_validate(instance)
