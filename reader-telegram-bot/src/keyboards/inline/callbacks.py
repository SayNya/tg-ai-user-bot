from aiogram.filters.callback_data import CallbackData


class TopicCallbackFactory(CallbackData, prefix="topic"):
    action: str
    page: int = 0


class TopicListCallbackFactory(CallbackData, prefix="topiclist"):
    id: int


class TopicEditCallbackFactory(CallbackData, prefix="edit"):
    action: str
    id: int


class ChatCallbackFactory(CallbackData, prefix="chat"):
    action: str
    page: int = 0


class ChangeChatCallbackFactory(CallbackData, prefix="cg"):
    action: str
    id: int


class HandleChatTopic(CallbackData, prefix="handlechattopic"):
    action: str

    chat_id: int

    topic_id: int | None = None

    page: int = 0
    page_size: int = 5


class PaymentCallbackFactory(CallbackData, prefix="payment"):
    action: str
    amount: int | None = None


class ReportCallbackFactory(CallbackData, prefix="report"):
    period: str
