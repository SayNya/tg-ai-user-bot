from .base import BaseDBModel


class TelegramAuthDBBase(BaseDBModel):
    """Database model for TelegramAuth entity."""

    api_id: int
    api_hash: str
    phone: str
    session_string: str | None = None
    user_id: int


class TelegramAuthCreateDB(TelegramAuthDBBase):
    """Database model for creating a new TelegramAuth."""


class TelegramAuthDB(TelegramAuthDBBase):
    """Database model for TelegramAuth entity."""

    id: int
