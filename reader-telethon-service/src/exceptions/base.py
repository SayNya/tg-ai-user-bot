from typing import Any


class BaseError(Exception):
    def __init__(
        self,
        *_: tuple[Any],
        message: str = "",
    ) -> None:
        self.message: str = message

        super().__init__(message)
