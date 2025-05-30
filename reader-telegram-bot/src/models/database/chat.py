from .base import BaseDBModel, TimestampedModel


class ChatDBBase(BaseDBModel):
    """Base model for Chat entity."""

    telegram_chat_id: int
    name: str
    is_active: bool = True
    user_id: int


class ChatCreateDB(ChatDBBase):
    """Model for creating a new Chat."""


class ChatDB(ChatDBBase, TimestampedModel):
    """Model for reading/returning Chat data."""

    id: int
