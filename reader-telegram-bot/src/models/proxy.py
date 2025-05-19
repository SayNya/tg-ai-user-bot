from datetime import datetime

from pydantic import BaseModel, ConfigDict

__all__ = ["ProxyBase", "ProxyCreate", "ProxyOut"]


class ProxyBase(BaseModel):
    host: str
    port: int
    username: str | None = None
    password: str | None = None


class ProxyCreate(ProxyBase):
    pass


class ProxyOut(ProxyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
