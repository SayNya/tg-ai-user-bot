from enum import Enum


class RabbitMQQueuePublisher(str, Enum):
    # Registration queues
    REGISTRATION_STATUS = "registration.status"

    # Message queues
    MESSAGE_PROCESS = "message.process"
    MESSAGE_PROCESS_THREAD = "message.process.thread"

    # Client queues
    CLIENT_STARTED = "telegram.client.started"
    CLIENT_STOPPED = "telegram.client.stopped"
    CLIENT_STATUS = "telegram.client.status"
    CLIENT_ERROR = "telegram.client.error"
    CLIENT_CHAT_LIST = "telegram.client.chat.list"


class RabbitMQQueueConsumer(str, Enum):
    # Registration queues
    REGISTRATION_INIT = "registration.init"
    REGISTRATION_CONFIRM = "registration.confirm"
    REGISTRATION_PASSWORD = "registration.password"

    # Message queues
    MESSAGE_ANSWER = "message.answer"
    MESSAGE_PROCESS_THREAD = "message.process.thread"

    # Client queues
    CLIENT_START = "telegram.client.start"
    CLIENT_STOP = "telegram.client.stop"
    CLIENT_CHAT_LIST = "telegram.client.chat.list.get"
