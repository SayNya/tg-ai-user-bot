from pydantic import BaseModel

from .base import TimestampedModel


class MessageBase(BaseModel):
    """Base model for Message entity."""

    telegram_message_id: int
    sender_type: str
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    parent_message_id: int | None = None
    thread_id: int


class MessageCreate(MessageBase):
    """Model for creating a new Message."""


class Message(MessageBase, TimestampedModel):
    """Model for Message entity."""

    id: int
