from pydantic import BaseModel

from .base import TimestampedModel


class TopicBase(BaseModel):
    """Base model for Topic entity."""

    name: str
    description: str | None = None
    prompt: str | None = None
    user_id: int


class TopicCreate(TopicBase):
    """Model for creating a new Topic."""


class Topic(TopicBase, TimestampedModel):
    """Model for Topic entity."""

    id: int
