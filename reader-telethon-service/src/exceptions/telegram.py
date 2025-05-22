from typing import Any

from .base import BaseError


# Registration errors
class RegistrationError(BaseError):
    def __init__(
        self,
        *_: tuple[Any],
        message: str = "Registration error",
    ) -> None:
        super().__init__(message=message)


class AuthDataExpiredError(RegistrationError):
    def __init__(
        self,
        *_: tuple[Any],
        message: str = "Auth data expired",
    ) -> None:
        super().__init__(message=message)


class TelegramClientError(RegistrationError):
    def __init__(
        self,
        *_: tuple[Any],
        message: str = "Telegram client error",
    ) -> None:
        super().__init__(message=message)


# Manager errors
class ClientManagerError(BaseError):
    def __init__(
        self,
        *_: tuple[Any],
        message: str = "Client manager error",
    ) -> None:
        super().__init__(message=message)


class ClientNotFoundError(ClientManagerError):
    def __init__(
        self,
        *_: tuple[Any],
        message: str = "Client not found",
    ) -> None:
        super().__init__(message=message)
