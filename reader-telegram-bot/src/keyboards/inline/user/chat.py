import aiogram

from src.keyboards.inline.callbacks import (
    ChangeChatCallbackFactory,
    ChatCallbackFactory,
)
from src.keyboards.inline.consts import InlineConstructor
from src.models.database import ChatDB
from src.models.rabbitmq import Chat


class ChatButtons(InlineConstructor):
    @staticmethod
    def main() -> aiogram.types.InlineKeyboardMarkup:
        actions = [
            {
                "text": "Добавить группу",
                "cb": ChatCallbackFactory(action="add"),
            },
            {
                "text": "Удалить группу",
                "cb": ChatCallbackFactory(action="delete"),
            },
        ]
        schema = [1, 1]
        return ChatButtons._create_kb(actions, schema)

    @staticmethod
    def chats(
        chats: list[Chat] | list[ChatDB],
        action: str,
        page: int,
        page_size: int = 5,
    ) -> aiogram.types.InlineKeyboardMarkup:
        start = page * page_size
        end = start + page_size
        paginated_chats = chats[start:end]

        actions = [
            {
                "text": chat.name,
                "cb": ChangeChatCallbackFactory(
                    id=chat.id,
                    action=action,
                ),
            }
            for chat in paginated_chats
        ]

        # Add pagination buttons
        if page > 0:
            actions.append(
                {
                    "text": "⬅️ Предыдущая",
                    "cb": ChatCallbackFactory(action=action, page=page - 1),
                },
            )
        if end < len(chats):
            actions.append(
                {
                    "text": "➡️ Следующая",
                    "cb": ChatCallbackFactory(action=action, page=page + 1),
                },
            )

        schema = [1] * len(paginated_chats)
        if len(actions) > len(paginated_chats):
            schema.append(len(actions) - len(paginated_chats))

        return ChatButtons._create_kb(actions, schema)
