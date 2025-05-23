from src.exceptions.database import (
    DatabaseError,
    DatabaseNotFoundError,
    DatabaseUnprocessableError,
)
from src.exceptions.telegram import (
    AuthDataExpiredError,
    ClientManagerError,
    ClientNotFoundError,
    RegistrationError,
    TelegramClientError,
)

__all__ = [
    "AuthDataExpiredError",
    "ClientManagerError",
    "ClientNotFoundError",
    "DatabaseError",
    "DatabaseNotFoundError",
    "DatabaseUnprocessableError",
    "RegistrationError",
    "TelegramClientError",
]
