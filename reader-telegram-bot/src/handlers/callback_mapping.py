from aiogram import F

from src.handlers.user import (
    chat,
    chat_handle,
    registration,
    report,
    topic,
)
from src.keyboards.inline import callbacks

callback_action_mapping = [
    # Chat actions
    (
        chat.choose_chat_to_add,
        callbacks.ChatCallbackFactory.filter(F.action == "add"),
    ),
    (
        chat.choose_chat_to_delete,
        callbacks.ChatCallbackFactory.filter(F.action == "delete"),
    ),
    (chat.add_chat, callbacks.ChangeChatCallbackFactory.filter(F.action == "add")),
    (
        chat.delete_chat,
        callbacks.ChangeChatCallbackFactory.filter(F.action == "delete"),
    ),
    # Topic actions
    (topic.add_topic, callbacks.TopicCallbackFactory.filter(F.action == "add")),
    (
        topic.choose_topic_to_edit,
        callbacks.TopicCallbackFactory.filter(F.action == "edit"),
    ),
    (
        topic.edit_topic,
        callbacks.TopicListCallbackFactory.filter(),
    ),
    (
        topic.delete_topic,
        callbacks.TopicEditCallbackFactory.filter(F.action == "delete"),
    ),
    (
        topic.input_topic_field_to_edit,
        callbacks.TopicEditCallbackFactory.filter(F.action == "edit_name"),
    ),
    (
        topic.input_topic_field_to_edit,
        callbacks.TopicEditCallbackFactory.filter(F.action == "edit_description"),
    ),
    (
        topic.input_topic_field_to_edit,
        callbacks.TopicEditCallbackFactory.filter(F.action == "edit_prompt"),
    ),
    # Handle chat topics
    (
        chat_handle.handle_topic_selection,
        callbacks.HandleChatTopic.filter(F.action == "handle"),
    ),
    (
        chat_handle.toggle_topic_selection,
        callbacks.HandleChatTopic.filter(F.action == "toggle"),
    ),
    (
        chat_handle.paginate_topics,
        callbacks.HandleChatTopic.filter(F.action == "paginate"),
    ),
    (
        chat_handle.confirm_binding,
        callbacks.HandleChatTopic.filter(F.action == "confirm"),
    ),
    # Report actions
    (report.generate_report, callbacks.ReportCallbackFactory.filter(F.period == "day")),
    (
        report.generate_report,
        callbacks.ReportCallbackFactory.filter(F.period == "week"),
    ),
    (
        report.generate_report,
        callbacks.ReportCallbackFactory.filter(F.period == "month"),
    ),
    # Registration actions
    (registration.handle_back_or_cancel, F.data == "registration:back"),
    (registration.handle_back_or_cancel, F.data == "registration:cancel"),
    # Payment actions
    # (
    #     payment.toggle_subscription,
    #     callbacks.PaymentCallbackFactory.filter(F.action == "toggle_subscription"),
    # ),
    # (
    #     payment.enter_amount,
    #     callbacks.PaymentCallbackFactory.filter(F.action == "enter_amount"),
    # ),
]
