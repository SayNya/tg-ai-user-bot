from aiogram import F

from src.tg_bot.handlers.user import group, group_handle, payment, registration
from src.tg_bot.keyboards.inline.callbacks import (
    ChangeGroupCallbackFactory,
    GroupCallbackFactory,
    HandleGroupTheme,
    PaymentCallbackFactory,
)

callback_action_mapping = [
    # Group actions
    (group.choose_group_to_add, GroupCallbackFactory.filter(F.action == "add")),
    (group.choose_group_to_delete, GroupCallbackFactory.filter(F.action == "delete")),
    (group.add_group, ChangeGroupCallbackFactory.filter(F.action == "add")),
    (group.delete_group, ChangeGroupCallbackFactory.filter(F.action == "delete")),
    # Handle group themes
    (group_handle.handle_theme, HandleGroupTheme.filter(F.action == "handle_theme")),
    (group_handle.save_handle, HandleGroupTheme.filter(F.action == "save")),
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
