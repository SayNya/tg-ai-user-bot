import aiogram

from src.models import TopicOut
from src.tg_bot.keyboards.inline.callbacks import (
    HandleGroupTheme,
    ThemeCallbackFactory,
    ThemeEditCallbackFactory,
    ThemeListCallbackFactory,
)
from src.tg_bot.keyboards.inline.consts import InlineConstructor


class TopicButtons(InlineConstructor):
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
        return TopicButtons._create_kb(actions, schema)

    @staticmethod
    def topics(
        topics: list[TopicOut],
        page: int,
        page_size: int = 5,
    ) -> aiogram.types.InlineKeyboardMarkup:
        start = page * page_size
        end = start + page_size
        paginated_themes = topics[start:end]
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
                },
            )
        if end < len(topics):
            actions.append(
                {
                    "text": "➡️ Следующая",
                    "cb": ThemeCallbackFactory(action="edit", page=page + 1),
                },
            )

        schema = [1] * len(paginated_themes)
        if len(actions) > len(paginated_themes):
            schema.append(len(actions) - len(paginated_themes))

        return TopicButtons._create_kb(actions, schema)

    @staticmethod
    def edit_topic(topic: TopicOut) -> aiogram.types.InlineKeyboardMarkup:
        actions = [
            {
                "text": "Изменить название",
                "cb": ThemeEditCallbackFactory(
                    id=topic.id,
                    action="edit_name",
                ),
            },
            {
                "text": "Изменить описание",
                "cb": ThemeEditCallbackFactory(
                    id=topic.id,
                    action="edit_description",
                ),
            },
            {
                "text": "Изменить промпт",
                "cb": ThemeEditCallbackFactory(
                    id=topic.id,
                    action="edit_prompt",
                ),
            },
            {
                "text": "Удалить тему",
                "cb": ThemeEditCallbackFactory(
                    id=topic.id,
                    action="delete",
                ),
            },
        ]
        schema = [1, 1, 1, 1]
        return TopicButtons._create_kb(actions, schema)

    @staticmethod
    def group_theme_selection(
        group_id: int,
        themes: list[TopicOut],
        existing_themes: list[TopicOut],
        selected_themes: list[TopicOut] | None = None,
        page: int = 0,
        page_size: int = 5,
    ) -> aiogram.types.InlineKeyboardMarkup:
        if selected_themes is None:
            selected_themes = []

        start = page * page_size
        end = start + page_size
        paginated_themes = themes[start:end]

        buttons = []

        for theme in paginated_themes:
            # Выбираем тему, если она есть в одном из списков, но не в обоих одновременно
            # (например, уже привязана, но не выбрана — или наоборот)
            is_selected = (theme.id in existing_themes) != (theme.id in selected_themes)

            buttons.append(
                {
                    "text": f"{'✅ ' if is_selected else ''}{theme.name}",
                    "callback_data": HandleGroupTheme(
                        group_id=group_id,
                        theme_id=theme.id,
                        action="toggle",
                        page=page,
                        page_size=page_size,
                    ),
                },
            )

        # Добавляем кнопки пагинации
        if page > 0:
            buttons.append(
                {
                    "text": "⬅️ Предыдущая",
                    "callback_data": HandleGroupTheme(
                        group_id=group_id,
                        page=page - 1,
                        page_size=page_size,
                        action="paginate",
                    ),
                },
            )
        if end < len(themes):
            buttons.append(
                {
                    "text": "➡️ Следующая",
                    "callback_data": HandleGroupTheme(
                        group_id=group_id,
                        page=page + 1,
                        page_size=page_size,
                        action="paginate",
                    ),
                },
            )

        # Добавляем кнопку подтверждения
        buttons.append(
            {
                "text": "Сохранить",
                "callback_data": HandleGroupTheme(group_id=group_id, action="confirm"),
            },
        )

        # Схема кнопок: одна кнопка на строку
        schema = [1] * len(paginated_themes)
        if len(buttons) > len(paginated_themes):
            schema.append(len(buttons) - len(paginated_themes))

        return TopicButtons._create_kb(buttons, schema)
