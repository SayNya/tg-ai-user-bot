from datetime import datetime

from pydantic import BaseModel, ConfigDict

__all__ = ["TopicBase", "TopicCreate", "TopicOut"]


class TopicBase(BaseModel):
    name: str
    description: str | None
    prompt: str | None


class TopicCreate(TopicBase):
    user_id: int


class TopicOut(TopicBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    user_id: int
