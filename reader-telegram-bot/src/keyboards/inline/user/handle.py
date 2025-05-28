import aiogram

from src.keyboards.inline.callbacks import HandleChatTopic
from src.keyboards.inline.consts import InlineConstructor
from src.models.database import ChatDB, TopicDB


class HandleButtons(InlineConstructor):
    @staticmethod
    def chats_buttons(chats: list[ChatDB]) -> aiogram.types.InlineKeyboardMarkup:
        actions = []
        schema = []
        for chat in chats:
            actions.append(
                {
                    "text": chat.title,
                    "cb": HandleChatTopic(action="handle", chat_id=chat.id),
                },
            )
            if not schema or schema[-1] == 3:
                schema.append(1)
            else:
                schema[-1] += 1
        return HandleButtons._create_kb(actions, schema)

    @staticmethod
    def topics_buttons(
        topics: list[TopicDB],
        chat_id: int,
    ) -> aiogram.types.InlineKeyboardMarkup:
        actions = []
        schema = []
        for topic in topics:
            actions.append(
                {
                    "text": topic.name,
                    "cb": HandleChatTopic(
                        action="save",
                        chat_id=chat_id,
                        topic_id=topic.id,
                    ),
                },
            )
            if not schema or schema[-1] == 3:
                schema.append(1)
            else:
                schema[-1] += 1
        return HandleButtons._create_kb(actions, schema)
