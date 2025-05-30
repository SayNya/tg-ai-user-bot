from datetime import datetime

from pydantic import BaseModel


class Topic(BaseModel):
    id: int
    name: str
    description: str
    prompt: str


class Message(BaseModel):
    telegram_message_id: int
    user_id: int
    chat_id: int
    text: str
    sender_username: str
    sender_id: int
    created_at: datetime


class AnswerTask(BaseModel):
    telegram_message_id: int
    user_id: int
    chat_id: int
    text: str
    topic_id: int
    score: float
    sender_username: str
    sender_id: int
    created_at: datetime
