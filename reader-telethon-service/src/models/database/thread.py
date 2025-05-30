from datetime import datetime

from .base import BaseDBModel


class ThreadBase(BaseDBModel):
    """Database model for Thread entity."""

    initiator_id: int
    initiator_username: str
    chat_id: int
    topic_id: int
    confidence_score: float
    last_activity_at: datetime


class ThreadCreate(ThreadBase):
    """Database model for creating a new Thread."""


class Thread(ThreadBase):
    """Database model for Thread entity."""

    id: int
