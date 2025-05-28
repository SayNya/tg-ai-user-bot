from datetime import datetime

from pydantic import BaseModel, ConfigDict

__all__ = ["ChatBase", "ChatCreate", "ChatOut", "ChatTest"]


class ChatBase(BaseModel):
    telegram_chat_id: int
    title: str | None
    is_active: bool = True


class ChatCreate(ChatBase):
    user_id: int


class ChatOut(ChatBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    user_id: int


class ChatTest(BaseModel):
    id: int
    title: str
