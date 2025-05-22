import aiogram

from src.tg_bot.keyboards.inline.callbacks import (
    ReportCallbackFactory,
)
from src.tg_bot.keyboards.inline.consts import InlineConstructor


class ReportButtons(InlineConstructor):
    @staticmethod
    def main() -> aiogram.types.InlineKeyboardMarkup:
        actions = [
            {
                "text": "1 день",
                "cb": ReportCallbackFactory(period="day"),
            },
            {
                "text": "1 неделя",
                "cb": ReportCallbackFactory(period="week"),
            },
            {
                "text": "1 месяц",
                "cb": ReportCallbackFactory(period="month"),
            },
        ]
        schema = [3]
        return ReportButtons._create_kb(actions, schema)
