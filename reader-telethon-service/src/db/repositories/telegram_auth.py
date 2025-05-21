from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import TelegramAuth
from src.models.database import TelegramAuth as TelegramAuthModel
from src.models.database import TelegramAuthCreate

from .base import BaseRepository


class TelegramAuthRepository(BaseRepository[TelegramAuth]):
    schema_class = TelegramAuth

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)

    async def all(self) -> AsyncGenerator[TelegramAuthModel, None]:
        async for instance in self._all():
            yield TelegramAuthModel.model_validate(instance)

    async def get(self, id_: int) -> TelegramAuthModel:
        instance = await self._get(key="id", value=id_)
        return TelegramAuthModel.model_validate(instance)

    async def create(self, schema: TelegramAuthCreate) -> TelegramAuthModel:
        instance = await self._save(schema.model_dump())
        return TelegramAuthModel.model_validate(instance)

    async def get_by_user_id(self, user_id: int) -> TelegramAuthModel | None:
        instance = await self._get(key="user_id", value=user_id)
        return TelegramAuthModel.model_validate(instance) if instance else None
