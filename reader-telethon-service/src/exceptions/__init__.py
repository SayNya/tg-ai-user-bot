from src.exceptions.database import (
    DatabaseError,
    DatabaseNotFoundError,
    DatabaseUnprocessableError,
)
from src.exceptions.telegram import (
    AuthDataExpiredError,
    RegistrationError,
    TelegramClientError,
)

__all__ = [
    "AuthDataExpiredError",
    "DatabaseError",
    "DatabaseNotFoundError",
    "DatabaseUnprocessableError",
    "RegistrationError",
    "TelegramClientError",
]
