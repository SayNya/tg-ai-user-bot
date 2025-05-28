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


class RabbitMQQueuePublisher(str, Enum):
    # Registration queues
    REGISTRATION_INIT = "registration.init"
    REGISTRATION_CONFIRM = "registration.confirm"
    REGISTRATION_PASSWORD = "registration.password"

    # Client queues
    CLIENT_START = "telegram.client.start"
    CLIENT_STOP = "telegram.client.stop"
    CLIENT_CHAT_LIST = "telegram.client.chat.list.get"


class RabbitMQQueueConsumer(str, Enum):
    # Registration queues
    REGISTRATION_STATUS = "registration.status"

    # Client queues
    CLIENT_STARTED = "telegram.client.started"
    CLIENT_STOPPED = "telegram.client.stopped"
    CLIENT_STATUS = "telegram.client.status"
    CLIENT_ERROR = "telegram.client.error"
    CLIENT_CHAT_LIST = "telegram.client.chat.list"
