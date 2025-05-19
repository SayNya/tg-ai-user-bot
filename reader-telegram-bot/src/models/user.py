from datetime import datetime

from pydantic import BaseModel, ConfigDict

__all__ = ["UserBase", "UserCreate", "UserOut"]


class UserBase(BaseModel):
    telegram_user_id: int
    username: str | None
    is_bot: bool = False
    first_name: str
    last_name: str | None
    language_code: str | None


class UserCreate(UserBase):
    proxy_id: int | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    proxy_id: int | None
