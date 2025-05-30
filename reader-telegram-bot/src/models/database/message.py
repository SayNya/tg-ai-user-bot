from .base import BaseDBModel, TimestampedModel
from .thread import ThreadWithChatTopicDB


class MessageDBBase(BaseDBModel):
    """Database model for Message entity."""

    telegram_message_id: int
    sender_type: str
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    parent_message_id: int | None = None
    thread_id: int


class MessageCreateDB(MessageDBBase):
    """Database model for creating a new Message."""


class MessageDB(MessageDBBase, TimestampedModel):
    """Database model for Message entity."""

    id: int


class DettailedMessageDB(MessageDB):
    thread: ThreadWithChatTopicDB
