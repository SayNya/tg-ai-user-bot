import aiogram

from src.models import ThemeModel
from src.tg_bot.keyboards.inline.callbacks import (
    ThemeEditCallbackFactory,
    ThemeListCallbackFactory,
    ThemeCallbackFactory,
)
from src.tg_bot.keyboards.inline.consts import InlineConstructor


class ThemeButtons(InlineConstructor):
    @staticmethod
    def main() -> aiogram.types.InlineKeyboardMarkup:
        actions = [
            {
                "text": "Добавить тему",
                "cb": ThemeCallbackFactory(action="add"),
            },
            {
                "text": "Изменить тему",
                "cb": ThemeCallbackFactory(action="edit"),
            },
        ]
        schema = [1, 1]
        return ThemeButtons._create_kb(actions, schema)

    @staticmethod
    def themes(
        themes: list[ThemeModel],
        page: int,
        page_size: int = 5,
    ) -> aiogram.types.InlineKeyboardMarkup:
        start = page * page_size
        end = start + page_size
        paginated_themes = themes[start:end]
        actions = [
            {
                "text": theme.name,
                "cb": ThemeListCallbackFactory(
                    id=theme.id,
                ),
            }
            for theme in paginated_themes
        ]

        # Add pagination buttons
        if page > 0:
            actions.append(
                {
                    "text": "⬅️ Предыдущая",
                    "cb": ThemeCallbackFactory(action="edit", page=page - 1),
                }
            )
        if end < len(themes):
            actions.append(
                {
                    "text": "➡️ Следующая",
                    "cb": ThemeCallbackFactory(action="edit", page=page + 1),
                }
            )

        schema = [1] * len(paginated_themes)
        if len(actions) > len(paginated_themes):
            schema.append(len(actions) - len(paginated_themes))

        return ThemeButtons._create_kb(actions, schema)

    @staticmethod
    def edit_theme(theme: ThemeModel) -> aiogram.types.InlineKeyboardMarkup:
        actions = [
            {
                "text": "Изменить название",
                "cb": ThemeEditCallbackFactory(
                    id=theme.id,
                    action="edit_name",
                ),
            },
            {
                "text": "Изменить описание",
                "cb": ThemeEditCallbackFactory(
                    id=theme.id,
                    action="edit_description",
                ),
            },
            {
                "text": "Изменить промпт",
                "cb": ThemeEditCallbackFactory(
                    id=theme.id,
                    action="edit_prompt",
                ),
            },
            {
                "text": "Удалить тему",
                "cb": ThemeEditCallbackFactory(
                    id=theme.id,
                    action="delete",
                ),
            },
        ]
        schema = [1, 1, 1, 1]
        return ThemeButtons._create_kb(actions, schema)