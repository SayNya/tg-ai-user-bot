from collections.abc import AsyncGenerator
from typing import Any, Generic

from sqlalchemy import Result, asc, delete, desc, func, select, update
from sqlalchemy.exc import IntegrityError, PendingRollbackError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.tables import ConcreteTable
from src.exceptions import (
    DatabaseError,
    DatabaseNotFoundError,
    DatabaseUnprocessableError,
)


class BaseRepository(Generic[ConcreteTable]):
    _ERRORS = (IntegrityError, PendingRollbackError)
    schema_class: type[ConcreteTable]

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        if not self.schema_class:
            raise DatabaseUnprocessableError(
                message=("Can not initiate the class without schema_class attribute"),
            )

    async def _update(
        self,
        key: str,
        value: Any,
        payload: dict[str, Any],
    ) -> ConcreteTable:
        async with self._session_factory() as session:
            query = (
                update(self.schema_class)
                .where(getattr(self.schema_class, key) == value)
                .values(payload)
                .returning(self.schema_class)
            )
            result: Result = await session.execute(query)
            await session.flush()

            if not (schema := result.scalar_one_or_none()):
                raise DatabaseError

            return schema

    async def _get(self, key: str, value: Any) -> ConcreteTable:
        async with self._session_factory() as session:
            query = select(self.schema_class).where(
                getattr(self.schema_class, key) == value,
            )
            result: Result = await session.execute(query)

            if not (_result := result.scalars().one_or_none()):
                raise DatabaseNotFoundError

            return _result

    async def count(self) -> int:
        async with self._session_factory() as session:
            result: Result = await session.execute(func.count(self.schema_class.id))
            value = result.scalar()

            if not isinstance(value, int):
                raise DatabaseUnprocessableError(
                    message=(
                        "For some reason count function returned not an integer."
                        f"Value: {value}"
                    ),
                )

            return value

    async def _first(self, by: str = "id") -> ConcreteTable:
        async with self._session_factory() as session:
            result: Result = await session.execute(
                select(self.schema_class).order_by(asc(by)).limit(1),
            )

            if not (_result := result.scalar_one_or_none()):
                raise DatabaseNotFoundError

            return _result

    async def _last(self, by: str = "id") -> ConcreteTable:
        async with self._session_factory() as session:
            result: Result = await session.execute(
                select(self.schema_class).order_by(desc(by)).limit(1),
            )

            if not (_result := result.scalar_one_or_none()):
                raise DatabaseNotFoundError

            return _result

    async def _save(self, payload: dict[str, Any]) -> ConcreteTable:
        async with self._session_factory() as session:
            try:
                schema = self.schema_class(**payload)
                session.add(schema)
                await session.flush()
                await session.refresh(schema)
            except self._ERRORS:
                raise DatabaseError  # noqa: B904
            else:
                return schema

    async def _all(self) -> AsyncGenerator[ConcreteTable, None]:
        async with self._session_factory() as session:
            result: Result = await session.execute(select(self.schema_class))
            schemas = result.scalars().all()

            for schema in schemas:
                yield schema

    async def delete(self, id_: int) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(self.schema_class).where(self.schema_class.id == id_),
            )
            await session.flush()

    async def execute(self, query) -> Result:
        try:
            async with self._session_factory() as session:
                result = await session.execute(query)
        except self._ERRORS:
            raise DatabaseError  # noqa: B904
        else:
            return result
