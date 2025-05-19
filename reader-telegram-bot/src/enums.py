from enum import Enum


class SenderType(str, Enum):
    user = "user"
    bot = "bot"


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


class QueueName(str, Enum):
    TELEGRAM_INIT = "telegram.init"
    TELEGRAM_CONFIRM = "telegram.confirm"
    TELEGRAM_PASSWORD = "telegram.password"
    TELEGRAM_STATUS = "telegram.status"
