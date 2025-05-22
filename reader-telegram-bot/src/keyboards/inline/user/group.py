import aiogram

from src.models import ChatOut
from src.tg_bot.keyboards.inline.callbacks import (
    ChangeGroupCallbackFactory,
    GroupCallbackFactory,
)
from src.tg_bot.keyboards.inline.consts import InlineConstructor


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
        groups: list[ChatOut],
        action: str,
        page: int,
        page_size: int = 5,
    ) -> aiogram.types.InlineKeyboardMarkup:
        start = page * page_size
        end = start + page_size
        paginated_groups = groups[start:end]

        actions = [
            {
                "text": group.name,
                "cb": ChangeGroupCallbackFactory(
                    id=group.id,
                    action=action,
                ),
            }
            for group in paginated_groups
        ]

        # Add pagination buttons
        if page > 0:
            actions.append(
                {
                    "text": "⬅️ Предыдущая",
                    "cb": GroupCallbackFactory(action=action, page=page - 1),
                },
            )
        if end < len(groups):
            actions.append(
                {
                    "text": "➡️ Следующая",
                    "cb": GroupCallbackFactory(action=action, page=page + 1),
                },
            )

        schema = [1] * len(paginated_groups)
        if len(actions) > len(paginated_groups):
            schema.append(len(actions) - len(paginated_groups))

        return GroupButtons._create_kb(actions, schema)
