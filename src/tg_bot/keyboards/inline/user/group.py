import aiogram

from src.models import GroupModel
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
        groups: list[GroupModel],
        action: str,
    ) -> aiogram.types.InlineKeyboardMarkup:
        actions = []
        schema = []
        for group in groups:
            actions.append(
                {
                    "text": group.name,
                    "cb": ChangeGroupCallbackFactory(
                        id=group.id,
                        name=group.name,
                        action=action,
                    ),
                },
            )
            if not schema or schema[-1] == 3:
                schema.append(1)
            else:
                schema[-1] += 1
        actions.reverse()
        return GroupButtons._create_kb(actions, schema)
