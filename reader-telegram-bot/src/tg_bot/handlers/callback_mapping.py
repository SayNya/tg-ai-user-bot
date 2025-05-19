from aiogram import F

from src.tg_bot.handlers.user import (
    chat,
    chat_handle,
    payment,
    registration,
    report,
    topic,
)
from src.tg_bot.keyboards.inline import callbacks

callback_action_mapping = [
    # Group actions
    (
        chat.choose_group_to_add,
        callbacks.GroupCallbackFactory.filter(F.action == "add"),
    ),
    (
        chat.choose_group_to_delete,
        callbacks.GroupCallbackFactory.filter(F.action == "delete"),
    ),
    (chat.add_group, callbacks.ChangeGroupCallbackFactory.filter(F.action == "add")),
    (
        chat.delete_group,
        callbacks.ChangeGroupCallbackFactory.filter(F.action == "delete"),
    ),
    # Theme actions
    (topic.add_theme, callbacks.ThemeCallbackFactory.filter(F.action == "add")),
    (
        topic.choose_theme_to_edit,
        callbacks.ThemeCallbackFactory.filter(F.action == "edit"),
    ),
    (
        topic.edit_theme,
        callbacks.ThemeListCallbackFactory.filter(),
    ),
    (
        topic.delete_theme,
        callbacks.ThemeEditCallbackFactory.filter(F.action == "delete"),
    ),
    (
        topic.input_theme_field_to_edit,
        callbacks.ThemeEditCallbackFactory.filter(F.action == "edit_name"),
    ),
    (
        topic.input_theme_field_to_edit,
        callbacks.ThemeEditCallbackFactory.filter(F.action == "edit_description"),
    ),
    (
        topic.input_theme_field_to_edit,
        callbacks.ThemeEditCallbackFactory.filter(F.action == "edit_prompt"),
    ),
    # Handle group themes
    (
        chat_handle.handle_theme_selection,
        callbacks.HandleGroupTheme.filter(F.action == "handle"),
    ),
    (
        chat_handle.toggle_theme_selection,
        callbacks.HandleGroupTheme.filter(F.action == "toggle"),
    ),
    (
        chat_handle.paginate_themes,
        callbacks.HandleGroupTheme.filter(F.action == "paginate"),
    ),
    (
        chat_handle.confirm_binding,
        callbacks.HandleGroupTheme.filter(F.action == "confirm"),
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
    (
        payment.toggle_subscription,
        callbacks.PaymentCallbackFactory.filter(F.action == "toggle_subscription"),
    ),
    (
        payment.enter_amount,
        callbacks.PaymentCallbackFactory.filter(F.action == "enter_amount"),
    ),
]
