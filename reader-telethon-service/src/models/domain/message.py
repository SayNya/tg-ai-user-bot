from pydantic import BaseModel


class MessageModel(BaseModel):
    user_id: int
    chat_id: int
    telegram_message_id: int
    content: str
    topic_id: int
