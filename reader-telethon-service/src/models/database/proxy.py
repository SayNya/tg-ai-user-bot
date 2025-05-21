from pydantic import BaseModel

from .base import TimestampedModel


class ProxyBase(BaseModel):
    """Base model for Proxy entity."""

    host: str
    port: int
    username: str | None = None
    password: str | None = None


class ProxyCreate(ProxyBase):
    """Model for creating a new Proxy."""


class Proxy(ProxyBase, TimestampedModel):
    """Model for Proxy entity."""

    id: int
