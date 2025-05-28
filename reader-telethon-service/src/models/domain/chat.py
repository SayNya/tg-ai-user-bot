from pydantic import BaseModel


class ChatModel(BaseModel):
    id: int
    name: str
