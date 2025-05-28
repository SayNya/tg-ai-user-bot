import aiogram

from src.models import ChatTest
from src.keyboards.inline.callbacks import (
    ChangeGroupCallbackFactory,
    GroupCallbackFactory,
)
from src.keyboards.inline.consts import InlineConstructor


class GroupButtons(InlineConstructor):
    @staticmethod
    def main() -> aiogram.types.InlineKeyboardMarkup:
        actions = [
            {
                "text": "Добавить группу",
                "cb": GroupCallbackFactory(action="add"),
            },
            {
                "text": "Удалить группу",
                "cb": GroupCallbackFactory(action="delete"),
            },
        ]
        schema = [1, 1]
        return GroupButtons._create_kb(actions, schema)

    @staticmethod
    def groups(
        chats: list[ChatTest],
        action: str,
        page: int,
        page_size: int = 5,
    ) -> aiogram.types.InlineKeyboardMarkup:
        start = page * page_size
        end = start + page_size
        paginated_chats = chats[start:end]

        actions = [
            {
                "text": chat.title,
                "cb": ChangeGroupCallbackFactory(
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
                    "cb": GroupCallbackFactory(action=action, page=page - 1),
                },
            )
        if end < len(chats):
            actions.append(
                {
                    "text": "➡️ Следующая",
                    "cb": GroupCallbackFactory(action=action, page=page + 1),
                },
            )

        schema = [1] * len(paginated_chats)
        if len(actions) > len(paginated_chats):
            schema.append(len(actions) - len(paginated_chats))

        return GroupButtons._create_kb(actions, schema)
