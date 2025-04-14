from aiogram.filters.callback_data import CallbackData


class ThemeCallbackFactory(CallbackData, prefix="theme"):
    action: str
    page: int = 0


class ThemeListCallbackFactory(CallbackData, prefix="themelist"):
    id: int


class ThemeEditCallbackFactory(CallbackData, prefix="edit"):
    action: str
    id: int


class GroupCallbackFactory(CallbackData, prefix="group"):
    action: str
    page: int = 0


class ChangeGroupCallbackFactory(CallbackData, prefix="cg"):
    action: str
    id: int


class HandleGroupTheme(CallbackData, prefix="handlegrouptheme"):
    action: str

    group_id: int
    theme_id: int | None = None


class PaymentCallbackFactory(CallbackData, prefix="payment"):
    action: str
    amount: int | None = None
