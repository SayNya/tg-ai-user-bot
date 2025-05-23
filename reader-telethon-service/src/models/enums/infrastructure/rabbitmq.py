from enum import Enum


class RabbitMQQueuePublisher(str, Enum):
    # Registration queues
    REGISTRATION_STATUS = "registration.status"

    # Message queues
    MESSAGE_PROCESS = "message.process"

    # Client queues
    CLIENT_STARTED = "telegram.client.started"
    CLIENT_STOPPED = "telegram.client.stopped"
    CLIENT_STATUS = "telegram.client.status"
    CLIENT_ERROR = "telegram.client.error"


class RabbitMQQueueConsumer(str, Enum):
    # Registration queues
    REGISTRATION_INIT = "registration.init"
    REGISTRATION_CONFIRM = "registration.confirm"
    REGISTRATION_PASSWORD = "registration.password"

    # Message queues
    MESSAGE_ANSWER = "message.answer"

    # Client queues
    CLIENT_START = "telegram.client.start"
    CLIENT_STOP = "telegram.client.stop"
