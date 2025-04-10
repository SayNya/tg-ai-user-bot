from aiogram.filters.callback_data import CallbackData


class GroupCallbackFactory(CallbackData, prefix="group"):
    action: str
    page: int = 0


class ChangeGroupCallbackFactory(CallbackData, prefix="cg"):
    action: str

    id: int


class ThemeCallbackFactory(CallbackData, prefix="theme"):
    action: str


class HandleGroupTheme(CallbackData, prefix="handlegrouptheme"):
    action: str

    group_id: int
    theme_id: int | None = None


class PaymentCallbackFactory(CallbackData, prefix="payment"):
    action: str
    amount: int | None = None
