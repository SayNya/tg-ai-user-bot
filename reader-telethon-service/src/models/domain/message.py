from datetime import datetime

from pydantic import BaseModel


class MessageBaseModel(BaseModel):
    telegram_message_id: int
    user_id: int
    chat_id: int
    text: str
    sender_username: str
    sender_id: int
    created_at: datetime


class MessageFromLLM(MessageBaseModel):
    topic_id: int
    score: float


class MessageFromTelethon(MessageBaseModel):
    thread_id: int
    reply_to_msg_id: int | None
