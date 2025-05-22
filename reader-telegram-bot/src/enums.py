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
    REGISTRATION_INIT = "registration.init"
    REGISTRATION_CONFIRM = "registration.confirm"
    REGISTRATION_PASSWORD = "registration.password"

    TELEGRAM_STATUS = "telegram.client.status"
