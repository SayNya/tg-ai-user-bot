from datetime import datetime

from .base import BaseDBModel
from .chat import ChatDB
from .topic import TopicDB


class ThreadDBBase(BaseDBModel):
    """Database model for Thread entity."""

    initiator_id: int
    initiator_username: str
    chat_id: int
    topic_id: int
    confidence_score: float
    last_activity_at: datetime


class ThreadCreateDB(ThreadDBBase):
    """Database model for creating a new Thread."""


class ThreadDB(ThreadDBBase):
    """Database model for Thread entity."""

    id: int


class ThreadWithChatTopicDB(ThreadDB):
    chat: ChatDB
    topic: TopicDB
