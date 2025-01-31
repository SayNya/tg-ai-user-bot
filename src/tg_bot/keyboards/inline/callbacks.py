from aiogram.filters.callback_data import CallbackData


class GroupCallbackFactory(CallbackData, prefix="group"):
    action: str


class ChangeGroupCallbackFactory(CallbackData, prefix="cg"):
    action: str

    id: int
    name: str | None = None


class ThemeCallbackFactory(CallbackData, prefix="theme"):
    action: str


class HandleGroupTheme(CallbackData, prefix="handlegrouptheme"):
    action: str

    group_id: int
    theme_id: int | None = None
