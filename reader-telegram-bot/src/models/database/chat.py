from .base import BaseDBModel, TimestampedModel


class ChatDB(BaseDBModel):
    """Base model for Chat entity."""

    telegram_chat_id: int
    title: str
    is_active: bool = True
    user_id: int


class ChatCreateDB(ChatDB):
    """Model for creating a new Chat."""


class ChatDB(ChatDB, TimestampedModel):
    """Model for reading/returning Chat data."""

    id: int
