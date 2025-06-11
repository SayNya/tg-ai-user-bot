import aiogram

from src.keyboards.inline.callbacks import (
    HandleChatTopic,
    TopicCallbackFactory,
    TopicEditCallbackFactory,
    TopicListCallbackFactory,
)
from src.keyboards.inline.consts import InlineConstructor
from src.models.database import TopicDB


class TopicButtons(InlineConstructor):
    @staticmethod
    def main() -> aiogram.types.InlineKeyboardMarkup:
        actions = [
            {
                "text": "Добавить тему",
                "cb": TopicCallbackFactory(action="add"),
            },
            {
                "text": "Изменить тему",
                "cb": TopicCallbackFactory(action="edit"),
            },
        ]
        schema = [1, 1]
        return TopicButtons._create_kb(actions, schema)

    @staticmethod
    def topics(
        topics: list[TopicDB],
        page: int,
        page_size: int = 5,
    ) -> aiogram.types.InlineKeyboardMarkup:
        start = page * page_size
        end = start + page_size
        paginated_topics = topics[start:end]
        actions = [
            {
                "text": topic.name,
                "cb": TopicListCallbackFactory(
                    id=topic.id,
                ),
            }
            for topic in paginated_topics
        ]

        # Add pagination buttons
        if page > 0:
            actions.append(
                {
                    "text": "⬅️ Предыдущая",
                    "cb": TopicCallbackFactory(action="edit", page=page - 1),
                },
            )
        if end < len(topics):
            actions.append(
                {
                    "text": "➡️ Следующая",
                    "cb": TopicCallbackFactory(action="edit", page=page + 1),
                },
            )

        schema = [1] * len(paginated_topics)
        if len(actions) > len(paginated_topics):
            schema.append(len(actions) - len(paginated_topics))

        return TopicButtons._create_kb(actions, schema)

    @staticmethod
    def edit_topic(topic: TopicDB) -> aiogram.types.InlineKeyboardMarkup:
        actions = [
            {
                "text": "Изменить название",
                "cb": TopicEditCallbackFactory(
                    id=topic.id,
                    action="edit_name",
                ),
            },
            {
                "text": "Изменить описание",
                "cb": TopicEditCallbackFactory(
                    id=topic.id,
                    action="edit_description",
                ),
            },
            {
                "text": "Изменить промпт",
                "cb": TopicEditCallbackFactory(
                    id=topic.id,
                    action="edit_prompt",
                ),
            },
            {
                "text": "Изменить ключевые слова",
                "cb": TopicEditCallbackFactory(
                    id=topic.id,
                    action="edit_keywords",
                ),
            },
            {
                "text": "Удалить тему",
                "cb": TopicEditCallbackFactory(
                    id=topic.id,
                    action="delete",
                ),
            },
        ]
        schema = [1, 1, 1, 1]
        return TopicButtons._create_kb(actions, schema)

    @staticmethod
    def chat_topic_selection(
        chat_id: int,
        topics: list[TopicDB],
        bound_topic_ids: list[int],
        selected_topic_ids: list[int],
        page: int = 0,
        page_size: int = 5,
    ) -> aiogram.types.InlineKeyboardMarkup:
        """Generate keyboard for topic selection with pagination."""
        start = page * page_size
        end = start + page_size
        paginated_topics = topics[start:end]

        buttons = []

        for topic in paginated_topics:
            # A topic is selected if it's in selected_topic_ids XOR in bound_topic_ids
            is_selected = (topic.id in bound_topic_ids) != (
                topic.id in selected_topic_ids
            )

            buttons.append(
                {
                    "text": f"{'✅ ' if is_selected else ''}{topic.name}",
                    "callback_data": HandleChatTopic(
                        chat_id=chat_id,
                        topic_id=topic.id,
                        action="toggle",
                        page=page,
                        page_size=page_size,
                    ),
                },
            )

        # Add pagination buttons
        if page > 0:
            buttons.append(
                {
                    "text": "⬅️ Предыдущая",
                    "callback_data": HandleChatTopic(
                        chat_id=chat_id,
                        page=page - 1,
                        page_size=page_size,
                        action="paginate",
                    ),
                },
            )
        if end < len(topics):
            buttons.append(
                {
                    "text": "➡️ Следующая",
                    "callback_data": HandleChatTopic(
                        chat_id=chat_id,
                        page=page + 1,
                        page_size=page_size,
                        action="paginate",
                    ),
                },
            )

        # Add confirmation button
        buttons.append(
            {
                "text": "Сохранить",
                "callback_data": HandleChatTopic(chat_id=chat_id, action="confirm"),
            },
        )

        # One button per row
        schema = [1] * len(paginated_topics)
        if len(buttons) > len(paginated_topics):
            schema.append(len(buttons) - len(paginated_topics))

        return TopicButtons._create_kb(buttons, schema)
