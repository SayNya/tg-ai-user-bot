import orjson
from aio_pika import IncomingMessage
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from src.data import settings
from src.enums import QueueName, RegistrationStatus
from src.rabbitmq import register_consumer
from src.tg_bot.states.user import UserRegistration


@register_consumer(QueueName.TELEGRAM_STATUS)
async def handle_registration_status(
    message: IncomingMessage,
    bot: Bot,
    dispatcher: Dispatcher,
) -> None:
    async with message.process():
        data = orjson.loads(message.body)
        user_id = data["user_id"]
        status = data["status"]

        state = FSMContext(
            storage=dispatcher.fsm.storage,
            key=StorageKey(bot_id=settings.bot.id, chat_id=user_id, user_id=user_id),
        )

        state_data = await state.get_data()
        working_message_id = state_data.get("working_message_id")

        if status == RegistrationStatus.CODE_SENT.value:
            await bot.edit_message_text(
                """🔹 Введите код подтверждения 🔹

Пожалуйста, укажите код, который пришел вам в Telegram, в формате:
📌 "123_45"

❗ Обратите внимание на нижнее подчеркивание между числами!""",
                chat_id=user_id,
                message_id=working_message_id,
            )

            await state.set_state(UserRegistration.tg_code)
        elif status == RegistrationStatus.PASSWORD_REQUIRED.value:
            await bot.edit_message_text(
                "Введите 2fa пароль:",
                chat_id=user_id,
                message_id=working_message_id,
            )
            await state.set_state(UserRegistration.password)
        elif status == RegistrationStatus.REGISTERED.value:
            await bot.edit_message_text(
                "✅ Регистрация успешно завершена! ✅",
                chat_id=user_id,
                message_id=working_message_id,
            )
            await state.clear()
        elif status == RegistrationStatus.ERROR.value:
            error = data.get("error", {})
            await bot.send_message(
                chat_id=user_id,
                text=f"❌ Ошибка: {error.get('message', 'Неизвестная ошибка')}",
            )
            await state.clear()
