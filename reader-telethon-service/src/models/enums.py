from enum import Enum


class RegistrationStatus(str, Enum):
    CODE_SENT = "code_sent"
    REGISTERED = "registered"
    PASSWORD_REQUIRED = "password_required"
    ERROR = "error"


class ErrorCode(str, Enum):
    AUTH_DATA_EXPIRED = "AUTH_DATA_EXPIRED"
    TELEGRAM_API_ERROR = "TELEGRAM_API_ERROR"
    INVALID_CODE = "INVALID_CODE"
    PASSWORD_REQUIRED = "PASSWORD_REQUIRED"
