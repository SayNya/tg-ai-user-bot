from types import MappingProxyType

from aiogram.enums import ChatType

from .base import BaseModel

CHAT_TYPE_MAPPING = MappingProxyType(
    {
        ChatType.PRIVATE: "private",
        # ChatType.BOT: "bot",
        ChatType.GROUP: "group",
        ChatType.SUPERGROUP: "supergroup",
        ChatType.CHANNEL: "channel",
    },
)


class GroupModel(BaseModel):
    id: int
    name: str
    type: str
