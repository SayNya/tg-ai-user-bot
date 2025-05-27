from pydantic import BaseModel

from src.models.enums import SenderType

from .base import TimestampedModel


class MessageBase(BaseModel):
    """Base model for Message entity."""

    telegram_message_id: int
    sender_type: SenderType
    sender_username: str | None = None
    content: str
    confidence_score: float | None = None
    chat_id: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    topic_id: int | None = None
    parent_message_id: int | None = None


class MessageCreate(MessageBase):
    """Model for creating a new Message."""


class Message(MessageBase, TimestampedModel):
    """Model for Message entity."""

    id: int
