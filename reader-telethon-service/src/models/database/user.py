from pydantic import BaseModel

from .base import TimestampedModel


class UserBase(BaseModel):
    """Base model for User entity."""

    telegram_user_id: int
    username: str | None = None
    is_bot: bool = False
    first_name: str
    last_name: str | None = None
    language_code: str | None = None
    proxy_id: int | None = None


class UserCreate(UserBase):
    """Model for creating a new User."""


class User(UserBase, TimestampedModel):
    """Model for User entity."""

    id: int
