from datetime import datetime

from .base import BaseModel


class MessageModel(BaseModel):
    id: int
    text: str
    chat_id: int
    user_id: int
    mentioned_id: int | None
    created_at: datetime
    sender_id: int
    theme_id: int
    sender_username: str | None
    

class DetailedMessageModel(BaseModel):
    id: int
    text: str
    chat_id: int
    chat_name: str
    theme_id: int | None
    theme_name: str | None
    sender_id: int
    sender_username: str | None
    created_at: datetime
