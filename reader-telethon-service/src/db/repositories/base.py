from collections.abc import AsyncGenerator
from typing import Any, Generic

import structlog
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

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self._session_factory = session_factory
        self.logger = logger
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
        self.logger.debug(
            "db_update_called",
            table=self.schema_class.__name__,
            key=key,
            value=value,
            payload=payload,
        )
        async with self._session_factory() as session:
            query = (
                update(self.schema_class)
                .where(getattr(self.schema_class, key) == value)
                .values(payload)
                .returning(self.schema_class)
            )
            try:
                result: Result = await session.execute(query)
                await session.flush()
                await session.commit()
                if not (schema := result.scalar_one_or_none()):
                    self.logger.error(
                        "db_update_not_found",
                        table=self.schema_class.__name__,
                        key=key,
                        value=value,
                    )
                    raise DatabaseError
                self.logger.debug(
                    "db_update_success",
                    table=self.schema_class.__name__,
                    key=key,
                    value=value,
                )
                return schema
            except Exception as e:
                self.logger.exception(
                    "db_update_error",
                    table=self.schema_class.__name__,
                    key=key,
                    value=value,
                    error=str(e),
                )
                raise

    async def _get(self, key: str, value: Any) -> ConcreteTable:
        self.logger.debug(
            "db_get_called",
            table=self.schema_class.__name__,
            key=key,
            value=value,
        )
        async with self._session_factory() as session:
            query = select(self.schema_class).where(
                getattr(self.schema_class, key) == value,
            )
            try:
                result: Result = await session.execute(query)
                if not (_result := result.scalars().one_or_none()):
                    self.logger.error(
                        "db_get_not_found",
                        table=self.schema_class.__name__,
                        key=key,
                        value=value,
                    )
                    raise DatabaseNotFoundError
                self.logger.debug(
                    "db_get_success",
                    table=self.schema_class.__name__,
                    key=key,
                    value=value,
                )
                return _result
            except Exception as e:
                self.logger.exception(
                    "db_get_error",
                    table=self.schema_class.__name__,
                    key=key,
                    value=value,
                    error=str(e),
                )
                raise

    async def count(self) -> int:
        self.logger.debug(
            "db_count_called",
            table=self.schema_class.__name__,
        )
        async with self._session_factory() as session:
            try:
                result: Result = await session.execute(func.count(self.schema_class.id))
                value = result.scalar()
                if not isinstance(value, int):
                    self.logger.error(
                        "db_count_type_error",
                        table=self.schema_class.__name__,
                        value=value,
                    )
                    raise DatabaseUnprocessableError(
                        message=(
                            "For some reason count function returned not an integer."
                            f"Value: {value}"
                        ),
                    )
                self.logger.debug(
                    "db_count_success",
                    table=self.schema_class.__name__,
                    count=value,
                )
                return value
            except Exception as e:
                self.logger.exception(
                    "db_count_error",
                    table=self.schema_class.__name__,
                    error=str(e),
                )
                raise

    async def _first(self, by: str = "id") -> ConcreteTable:
        self.logger.debug(
            "db_first_called",
            table=self.schema_class.__name__,
            by=by,
        )
        async with self._session_factory() as session:
            try:
                result: Result = await session.execute(
                    select(self.schema_class).order_by(asc(by)).limit(1),
                )
                if not (_result := result.scalar_one_or_none()):
                    self.logger.error(
                        "db_first_not_found",
                        table=self.schema_class.__name__,
                        by=by,
                    )
                    raise DatabaseNotFoundError
                self.logger.debug(
                    "db_first_success",
                    table=self.schema_class.__name__,
                    by=by,
                )
                return _result
            except Exception as e:
                self.logger.exception(
                    "db_first_error",
                    table=self.schema_class.__name__,
                    by=by,
                    error=str(e),
                )
                raise

    async def _last(self, by: str = "id") -> ConcreteTable:
        self.logger.debug(
            "db_last_called",
            table=self.schema_class.__name__,
            by=by,
        )
        async with self._session_factory() as session:
            try:
                result: Result = await session.execute(
                    select(self.schema_class).order_by(desc(by)).limit(1),
                )
                if not (_result := result.scalar_one_or_none()):
                    self.logger.error(
                        "db_last_not_found",
                        table=self.schema_class.__name__,
                        by=by,
                    )
                    raise DatabaseNotFoundError
                self.logger.debug(
                    "db_last_success",
                    table=self.schema_class.__name__,
                    by=by,
                )
                return _result
            except Exception as e:
                self.logger.exception(
                    "db_last_error",
                    table=self.schema_class.__name__,
                    by=by,
                    error=str(e),
                )
                raise

    async def _save(self, payload: dict[str, Any]) -> ConcreteTable:
        self.logger.debug(
            "db_save_called",
            table=self.schema_class.__name__,
            payload=payload,
        )
        async with self._session_factory() as session:
            try:
                schema = self.schema_class(**payload)
                session.add(schema)
                await session.flush()
                await session.refresh(schema)
                await session.commit()
                self.logger.debug(
                    "db_save_success",
                    table=self.schema_class.__name__,
                    id=getattr(schema, "id", None),
                )
                return schema
            except self._ERRORS as e:
                self.logger.exception(
                    "db_save_error",
                    table=self.schema_class.__name__,
                    payload=payload,
                    error=str(e),
                )
                raise DatabaseError  # noqa: B904

    async def _all(self) -> AsyncGenerator[ConcreteTable, None]:
        self.logger.debug(
            "db_all_called",
            table=self.schema_class.__name__,
        )
        async with self._session_factory() as session:
            try:
                result: Result = await session.execute(select(self.schema_class))
                schemas = result.scalars().all()
                self.logger.debug(
                    "db_all_success",
                    table=self.schema_class.__name__,
                    count=len(schemas),
                )
                for schema in schemas:
                    yield schema
            except Exception as e:
                self.logger.exception(
                    "db_all_error",
                    table=self.schema_class.__name__,
                    error=str(e),
                )
                raise

    async def delete(self, id_: int) -> None:
        self.logger.debug(
            "db_delete_called",
            table=self.schema_class.__name__,
            id=id_,
        )
        async with self._session_factory() as session:
            try:
                await session.execute(
                    delete(self.schema_class).where(self.schema_class.id == id_),
                )
                await session.flush()
                await session.commit()
                self.logger.debug(
                    "db_delete_success",
                    table=self.schema_class.__name__,
                    id=id_,
                )
            except Exception as e:
                self.logger.exception(
                    "db_delete_error",
                    table=self.schema_class.__name__,
                    id=id_,
                    error=str(e),
                )
                raise

    async def execute(self, query) -> Result:
        self.logger.debug(
            "db_execute_called",
            table=self.schema_class.__name__,
            query=str(query),
        )
        try:
            async with self._session_factory() as session:
                result = await session.execute(query)
                self.logger.debug(
                    "db_execute_success",
                    table=self.schema_class.__name__,
                )
                return result
        except self._ERRORS as e:
            self.logger.exception(
                "db_execute_error",
                table=self.schema_class.__name__,
                query=str(query),
                error=str(e),
            )
            raise DatabaseError  # noqa: B904
