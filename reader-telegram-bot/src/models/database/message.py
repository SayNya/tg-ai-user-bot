from .base import BaseDBModel, TimestampedModel


class MessageDB(BaseDBModel):
    """Database model for Message entity."""

    telegram_message_id: int
    sender_type: str
    content: str
    sender_username: str | None = None
    confidence_score: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    chat_id: int
    topic_id: int | None = None
    parent_message_id: int | None = None


class MessageCreateDB(MessageDB):
    """Database model for creating a new Message."""


class MessageDB(MessageDB, TimestampedModel):
    """Database model for Message entity."""

    id: int
