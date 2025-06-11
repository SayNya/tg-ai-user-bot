from .base import BaseDBModel, TimestampedModel


class TopicDBBase(BaseDBModel):
    """Database model for Topic entity."""

    name: str
    description: str
    prompt: str
    keywords: list[str] | None
    user_id: int


class TopicCreateDB(TopicDBBase):
    """Database model for creating a new Topic."""


class TopicDB(TopicDBBase, TimestampedModel):
    """Database model for Topic entity."""

    id: int
