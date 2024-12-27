import aiogram

from src.models import GroupModel
from src.models.theme import ThemeModel
from src.tg_bot.keyboards.inline.callbacks import HandleGroupTheme
from src.tg_bot.keyboards.inline.consts import InlineConstructor


class HandleButtons(InlineConstructor):
    @staticmethod
    def groups_buttons(groups: list[GroupModel]) -> aiogram.types.InlineKeyboardMarkup:
        actions = []
        schema = []
        for group in groups:
            actions.append(
                {
                    "text": group.name,
                    "cb": HandleGroupTheme(action="handle_theme", group_id=group.id),
                }
            )
            if not schema or schema[-1] == 3:
                schema.append(1)
            else:
                schema[-1] += 1
        return HandleButtons._create_kb(actions, schema)

    @staticmethod
    def themes_buttons(
        themes: list[ThemeModel],
        group_id: int,
    ) -> aiogram.types.InlineKeyboardMarkup:
        actions = []
        schema = []
        for theme in themes:
            actions.append(
                {
                    "text": theme.name,
                    "cb": HandleGroupTheme(
                        action="save", group_id=group_id, theme_id=theme.id
                    ),
                }
            )
            if not schema or schema[-1] == 3:
                schema.append(1)
            else:
                schema[-1] += 1
        return HandleButtons._create_kb(actions, schema)
