from aiogram.types import InlineKeyboardMarkup

from src.keyboards.inline.consts import InlineConstructor


class UserInlineButtons:
    @staticmethod
    def back(namespace: str) -> InlineKeyboardMarkup:
        schema = [1]
        actions = [{"text": "◀️ Назад", "callback_data": f"{namespace}:back"}]
        return InlineConstructor._create_kb(actions, schema)

    @staticmethod
    def cancel(namespace) -> InlineKeyboardMarkup:
        schema = [1]
        actions = [{"text": "🚫 Отменить", "callback_data": f"{namespace}:cancel"}]
        return InlineConstructor._create_kb(actions, schema)

    @staticmethod
    def back_and_cancel(namespace: str) -> InlineKeyboardMarkup:
        schema = []
        actions = []

        actions = [
            {"text": "◀️ Назад", "callback_data": f"{namespace}:back"},
            {"text": "🚫 Отменить", "callback_data": f"{namespace}:cancel"},
        ]

        schema = [1, 1]
        return InlineConstructor._create_kb(actions, schema)

    @staticmethod
    def confirmation(
        namespace: str,
        add_back: bool = False,
        add_cancel: bool = False,
    ) -> InlineKeyboardMarkup:
        schema = []
        actions = []
        if add_cancel:
            schema.append(1)
            actions.append(
                {"text": "🚫 Отменить", "callback_data": f"{namespace}:cancel"},
            )
        schema.append(1)
        actions.append(
            {"text": "✅ Подтвердить", "callback_data": f"{namespace}:confirm"},
        )
        if add_back:
            schema.append(1)
            actions.append({"text": "◀️ Назад", "callback_data": f"{namespace}:back"})
        return InlineConstructor._create_kb(actions, schema)

    @staticmethod
    def yes_n_no(
        namespace: str,
        add_back: bool = False,
        add_cancel: bool = False,
    ) -> InlineKeyboardMarkup:
        schema = [2]
        actions = [
            {"text": "✅Да", "callback_data": f"{namespace}:yes"},
            {"text": "❌Нет", "callback_data": f"{namespace}:no"},
        ]
        if add_back:
            schema.append(1)
            actions.append({"text": "◀️ Назад", "callback_data": f"{namespace}:back"})
        if add_cancel:
            schema.append(1)
            actions.append(
                {"text": "🚫 Отменить", "callback_data": f"{namespace}:cancel"},
            )
        return InlineConstructor._create_kb(actions, schema)
