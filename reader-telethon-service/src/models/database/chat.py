from pydantic import BaseModel

from .base import TimestampedModel


class ChatBase(BaseModel):
    """Base model for Chat entity."""

    telegram_chat_id: int
    title: str | None = None
    is_active: bool = True
    user_id: int


class ChatCreate(ChatBase):
    """Model for creating a new Chat."""


class Chat(ChatBase, TimestampedModel):
    """Model for Chat entity."""

    id: int
