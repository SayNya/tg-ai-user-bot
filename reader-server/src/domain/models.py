from datetime import datetime
from typing import Any

from pydantic import BaseModel


class Topic(BaseModel):
    id: int
    name: str
    description: str
    prompt: str


class Message(BaseModel):
    telegram_message_id: int
    user_id: str
    chat_id: str
    message_text: str
    sender_username: str | None = None
    created_at: datetime = datetime.now()


class AnswerTask(BaseModel):
    user_id: str
    chat_id: str
    telegram_message_id: int
    content: str
    topic_id: int
    score: float
    confidence_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "telegram_message_id": self.telegram_message_id,
            "content": self.content,
            "topic_id": self.topic_id,
            "score": self.score,
        }
