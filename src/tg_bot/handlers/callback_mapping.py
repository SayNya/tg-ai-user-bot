from aiogram import F

from src.tg_bot.handlers.user import (
    group,
    group_handle,
    payment,
    registration,
    report,
    theme,
)
from src.tg_bot.keyboards.inline import callbacks

callback_action_mapping = [
    # Group actions
    (
        group.choose_group_to_add,
        callbacks.GroupCallbackFactory.filter(F.action == "add"),
    ),
    (
        group.choose_group_to_delete,
        callbacks.GroupCallbackFactory.filter(F.action == "delete"),
    ),
    (group.add_group, callbacks.ChangeGroupCallbackFactory.filter(F.action == "add")),
    (
        group.delete_group,
        callbacks.ChangeGroupCallbackFactory.filter(F.action == "delete"),
    ),
    # Theme actions
    (theme.add_theme, callbacks.ThemeCallbackFactory.filter(F.action == "add")),
    (
        theme.choose_theme_to_edit,
        callbacks.ThemeCallbackFactory.filter(F.action == "edit"),
    ),
    (
        theme.edit_theme,
        callbacks.ThemeListCallbackFactory.filter(),
    ),
    (
        theme.delete_theme,
        callbacks.ThemeEditCallbackFactory.filter(F.action == "delete"),
    ),
    (
        theme.input_theme_field_to_edit,
        callbacks.ThemeEditCallbackFactory.filter(F.action == "edit_name"),
    ),
    (
        theme.input_theme_field_to_edit,
        callbacks.ThemeEditCallbackFactory.filter(F.action == "edit_description"),
    ),
    (
        theme.input_theme_field_to_edit,
        callbacks.ThemeEditCallbackFactory.filter(F.action == "edit_prompt"),
    ),
    # Handle group themes
    (
        group_handle.handle_theme_selection,
        callbacks.HandleGroupTheme.filter(F.action == "handle"),
    ),
    (
        group_handle.toggle_theme_selection,
        callbacks.HandleGroupTheme.filter(F.action == "toggle"),
    ),
    (
        group_handle.paginate_themes,
        callbacks.HandleGroupTheme.filter(F.action == "paginate"),
    ),
    (
        group_handle.confirm_binding,
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
    (registration.have_password, F.data == "registration:yes"),
    (registration.password_registration, F.data == "registration:no"),
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
