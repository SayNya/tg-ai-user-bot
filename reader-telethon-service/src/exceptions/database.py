from typing import Any

from .base import BaseError


class DatabaseError(BaseError):
    def __init__(
        self,
        *_: tuple[Any],
        message: str = "Database error",
    ) -> None:
        super().__init__(message=message)


class DatabaseNotFoundError(DatabaseError):
    def __init__(
        self,
        *_: tuple[Any],
        message: str = "Database not found",
    ) -> None:
        super().__init__(message=message)


class DatabaseUnprocessableError(DatabaseError):
    def __init__(
        self,
        *_: tuple[Any],
        message: str = "Database unprocessable",
    ) -> None:
        super().__init__(message=message)
