from aiogram.filters.callback_data import CallbackData


class GroupCallbackFactory(CallbackData, prefix="group"):
    action: str


class ChangeGroupCallbackFactory(CallbackData, prefix="changegroup"):
    action: str

    id: int
    name: str | None = None
    type: str | None = None
