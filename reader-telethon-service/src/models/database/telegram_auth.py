from pydantic import BaseModel

from .base import BaseDBModel
from .user import User


class TelegramAuthBase(BaseModel):
    """Base model for TelegramAuth entity."""

    api_id: int
    api_hash: str
    phone: str
    session_string: str | None = None
    user_id: int


class TelegramAuthCreate(TelegramAuthBase):
    """Model for creating a new TelegramAuth."""


class TelegramAuth(TelegramAuthBase, BaseDBModel):
    """Model for TelegramAuth entity."""

    id: int


class TelegramWithUser(TelegramAuthBase):
    """Model for TelegramAuth entity with User."""

    user: User
