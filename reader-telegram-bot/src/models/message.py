from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.enums import SenderType
from src.models.chat import ChatOut
from src.models.topic import TopicOut

__all__ = ["MessageBase", "MessageCreate", "MessageOut", "MessageWithTopicAndChat"]


class MessageBase(BaseModel):
    telegram_message_id: int
    sender_type: SenderType
    sender_username: str | None = None
    confidence_score: float | None
    content: str
    chat_id: int
    topic_id: int | None = None
    user_id: int | None = None
    parent_message_id: int | None = None


class MessageCreate(MessageBase):
    pass


class MessageOut(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class MessageWithTopicAndChat(MessageOut):
    topic: TopicOut | None
    chat: ChatOut | None
