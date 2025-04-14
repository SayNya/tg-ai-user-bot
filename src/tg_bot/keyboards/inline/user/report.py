import aiogram

from src.tg_bot.keyboards.inline.callbacks import (
    ThemeCallbackFactory,
)
from src.tg_bot.keyboards.inline.consts import InlineConstructor


class ReportButtons(InlineConstructor):
    @staticmethod
    def main() -> aiogram.types.InlineKeyboardMarkup:
        actions = [
            {
                "text": "1 день",
                "cb": ThemeCallbackFactory(action="add"),
            },
            {
                "text": "1 неделя",
                "cb": ThemeCallbackFactory(action="edit"),
            },
            {
                "text": "1 месяц",
                "cb": ThemeCallbackFactory(action="edit"),
            },
        ]
        schema = [1, 1, 1]
        return ReportButtons._create_kb(actions, schema)
