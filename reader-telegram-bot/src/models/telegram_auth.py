from pydantic import BaseModel, ConfigDict

__all__ = ["TelegramAuthBase", "TelegramAuthCreate", "TelegramAuthOut"]


class TelegramAuthBase(BaseModel):
    user_id: int
    api_id: int
    api_hash: str
    phone: str


class TelegramAuthCreate(TelegramAuthBase):
    pass


class TelegramAuthOut(TelegramAuthBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
