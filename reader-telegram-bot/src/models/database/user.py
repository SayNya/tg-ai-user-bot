from .base import BaseDBModel, TimestampedModel


class UserDB(BaseDBModel):
    """Database model for User entity."""

    id: int
    is_bot: bool = False
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    proxy_id: int | None = None


class UserCreateDB(UserDB):
    """Database model for creating a new User."""


class UserDB(UserDB, TimestampedModel):
    """Database model for User entity."""
