from .base import BaseDBModel, TimestampedModel


class ProxyDB(BaseDBModel):
    """Database model for Proxy entity."""

    host: str
    port: int
    username: str | None = None
    password: str | None = None


class ProxyCreateDB(ProxyDB):
    """Database model for creating a new Proxy."""


class ProxyDB(ProxyDB, TimestampedModel):
    """Database model for Proxy entity."""

    id: int
