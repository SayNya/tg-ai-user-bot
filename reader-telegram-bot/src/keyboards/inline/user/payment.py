from aiogram.types import InlineKeyboardMarkup

from src.tg_bot.keyboards.inline.callbacks import PaymentCallbackFactory
from src.tg_bot.keyboards.inline.consts import InlineConstructor


class PayButtons(InlineConstructor):
    @staticmethod
    def main(is_subscribed: bool) -> InlineKeyboardMarkup:
        actions = [
            {
                "text": "Отключить подписку" if is_subscribed else "Включить подписку",
                "cb": PaymentCallbackFactory(action="toggle_subscription"),
            },
            {
                "text": "Пополнить баланс",
                "cb": PaymentCallbackFactory(action="enter_amount"),
            },
        ]
        schema = [1, 1]
        return PayButtons._create_kb(actions, schema)
