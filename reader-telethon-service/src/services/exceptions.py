class RegistrationError(Exception):
    """Base exception for registration-related errors."""


class AuthDataExpiredError(RegistrationError):
    """Raised when authentication data has expired."""


class TelegramClientError(RegistrationError):
    """Raised when there's an error with the Telegram client."""
