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
