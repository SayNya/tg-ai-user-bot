from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseDBModel(BaseModel):
    """Base model for all database models."""

    model_config = ConfigDict(from_attributes=True)


class TimestampedModel(BaseDBModel):
    """Base model for entities with created_at timestamp."""

    created_at: datetime
