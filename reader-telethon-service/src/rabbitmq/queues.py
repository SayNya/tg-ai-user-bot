from enum import Enum


class QueueName(str, Enum):
    TELEGRAM_INIT = "telegram.init"
    TELEGRAM_CONFIRM = "telegram.confirm"
    TELEGRAM_PASSWORD = "telegram.password"
    TELEGRAM_STATUS = "telegram.status"
