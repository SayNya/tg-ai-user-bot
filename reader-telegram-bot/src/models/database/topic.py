from .base import BaseDBModel, TimestampedModel


class TopicDB(BaseDBModel):
    """Database model for Topic entity."""

    name: str
    description: str
    prompt: str
    user_id: int


class TopicCreateDB(TopicDB):
    """Database model for creating a new Topic."""


class TopicDB(TopicDB, TimestampedModel):
    """Database model for Topic entity."""

    id: int
