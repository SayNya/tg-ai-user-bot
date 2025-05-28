from .base import BaseRabbitMQModel


class Chat(BaseRabbitMQModel):
    """Chat model."""

    id: int
    name: str


class ClientChatList(BaseRabbitMQModel):
    """Client chat list message."""

    user_id: int
    chats: list[Chat]
