from aiogram import F

from src.tg_bot.handlers.user import group, group_handle, payment, registration, theme, report
from src.tg_bot.keyboards.inline.callbacks import (
    ChangeGroupCallbackFactory,
    GroupCallbackFactory,
    HandleGroupTheme,
    PaymentCallbackFactory,
    ReportCallbackFactory,
    ThemeCallbackFactory,
    ThemeEditCallbackFactory,
    ThemeListCallbackFactory,
)

callback_action_mapping = [
    # Group actions
    (group.choose_group_to_add, GroupCallbackFactory.filter(F.action == "add")),
    (group.choose_group_to_delete, GroupCallbackFactory.filter(F.action == "delete")),
    (group.add_group, ChangeGroupCallbackFactory.filter(F.action == "add")),
    (group.delete_group, ChangeGroupCallbackFactory.filter(F.action == "delete")),
    # Theme actions
    (theme.add_theme, ThemeCallbackFactory.filter(F.action == "add")),
    (theme.choose_theme_to_edit, ThemeCallbackFactory.filter(F.action == "edit")),
    (
        theme.edit_theme,
        ThemeListCallbackFactory.filter(),
    ),
    (theme.delete_theme, ThemeEditCallbackFactory.filter(F.action == "delete")),
    (
        theme.input_theme_field_to_edit,
        ThemeEditCallbackFactory.filter(F.action == "edit_name"),
    ),
    (
        theme.input_theme_field_to_edit,
        ThemeEditCallbackFactory.filter(F.action == "edit_description"),
    ),
    (
        theme.input_theme_field_to_edit,
        ThemeEditCallbackFactory.filter(F.action == "edit_prompt"),
    ),
    # Handle group themes
    (group_handle.handle_theme, HandleGroupTheme.filter(F.action == "handle_theme")),
    (group_handle.save_handle, HandleGroupTheme.filter(F.action == "save")),
    # Report actions
    (report.generate_report, ReportCallbackFactory.filter(F.period == "day")),
    (report.generate_report, ReportCallbackFactory.filter(F.period == "week")),
    (report.generate_report, ReportCallbackFactory.filter(F.period == "month")),
    # Registration actions
    (registration.handle_back_or_cancel, F.data == "registration:back"),
    (registration.handle_back_or_cancel, F.data == "registration:cancel"),
    (registration.have_password, F.data == "registration:yes"),
    (registration.password_registration, F.data == "registration:no"),
    # Payment actions
    (
        payment.toggle_subscription,
        PaymentCallbackFactory.filter(F.action == "toggle_subscription"),
    ),
    (payment.enter_amount, PaymentCallbackFactory.filter(F.action == "enter_amount")),
]
