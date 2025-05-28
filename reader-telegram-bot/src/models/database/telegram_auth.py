from .base import BaseDBModel


class TelegramAuthDB(BaseDBModel):
    """Database model for TelegramAuth entity."""

    api_id: int
    api_hash: str
    phone: str
    session_string: str | None = None
    user_id: int


class TelegramAuthCreateDB(TelegramAuthDB):
    """Database model for creating a new TelegramAuth."""


class TelegramAuthDB(TelegramAuthDB):
    """Database model for TelegramAuth entity."""

    id: int
