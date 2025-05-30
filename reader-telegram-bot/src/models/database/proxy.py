from .base import BaseDBModel, TimestampedModel


class ProxyDBBase(BaseDBModel):
    """Database model for Proxy entity."""

    host: str
    port: int
    username: str | None = None
    password: str | None = None


class ProxyCreateDB(ProxyDBBase):
    """Database model for creating a new Proxy."""


class ProxyDB(ProxyDBBase, TimestampedModel):
    """Database model for Proxy entity."""

    id: int
