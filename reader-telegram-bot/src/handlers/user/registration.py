from aiogram import Bot, types
from aiogram.fsm.context import FSMContext

from src.enums import RabbitMQQueuePublisher
from src.keyboards.inline import user
from src.rabbitmq.publisher import RabbitMQPublisher
from src.states.user import UserRegistration


async def start_registration(
    msg: types.Message,
    state: FSMContext,
) -> None:
    await state.set_state(UserRegistration.api_id)

    sent = await msg.answer(
        "🆔 Введите API ID 🆔\n\nhttps://my.telegram.org/auth?to=apps",
        reply_markup=user.UserInlineButtons.cancel(namespace="registration"),
    )
    await state.update_data(working_message_id=sent.message_id)


async def api_id_registration(
    msg: types.Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    await msg.delete()
    try:
        api_id = int(msg.text)
    except ValueError:
        await bot.edit_message_text(
            "⚠️ API ID должен быть числом ⚠️",
            chat_id=msg.chat.id,
            message_id=working_message_id,
            reply_markup=user.UserInlineButtons.cancel(namespace="registration"),
        )
        return

    await state.update_data(api_id=api_id)
    await state.set_state(UserRegistration.api_hash)

    await bot.edit_message_text(
        "🔑 Введите API Hash 🔑",
        chat_id=msg.chat.id,
        message_id=working_message_id,
        reply_markup=user.UserInlineButtons.back_and_cancel(namespace="registration"),
    )


async def api_hash_registration(
    msg: types.Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    await msg.delete()
    await state.update_data(api_hash=msg.text)
    await state.set_state(UserRegistration.phone)

    await bot.edit_message_text(
        "📱 Введите номер телефона 📱",
        chat_id=msg.chat.id,
        message_id=working_message_id,
        reply_markup=user.UserInlineButtons.back_and_cancel(namespace="registration"),
    )


async def register_client(
    msg: types.Message,
    state: FSMContext,
    publisher: RabbitMQPublisher,
    bot: Bot,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")
    await msg.delete()

    data = await state.get_data()
    user_id = msg.from_user.id

    payload = {
        "api_id": data["api_id"],
        "api_hash": data["api_hash"],
        "phone": msg.text,
        "user_id": user_id,
    }
    await publisher.publish(
        payload=payload,
        routing_key=RabbitMQQueuePublisher.REGISTRATION_INIT,
    )

    await bot.edit_message_text(
        "Подождите, идёт обработка",
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )


async def tg_code_registration(
    msg: types.Message,
    state: FSMContext,
    bot: Bot,
    publisher: RabbitMQPublisher,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")
    await msg.delete()

    user_id = msg.from_user.id

    tg_code = msg.text.split("_")
    if len(tg_code) != 2:
        await msg.answer("Неверный формат кода")
        return
    tg_code = "".join(tg_code)

    payload = {
        "code": tg_code,
        "user_id": user_id,
    }
    await publisher.publish(
        payload=payload,
        routing_key=RabbitMQQueuePublisher.REGISTRATION_CONFIRM,
    )

    await bot.edit_message_text(
        "Подождите, идёт обработка",
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )


async def password_registration(
    msg: types.Message,
    state: FSMContext,
    bot: Bot,
    publisher: RabbitMQPublisher,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    await msg.delete()

    user_id = msg.from_user.id

    payload = {
        "password": msg.text,
        "user_id": user_id,
    }
    await publisher.publish(
        payload=payload,
        routing_key=RabbitMQQueuePublisher.REGISTRATION_PASSWORD,
    )

    await bot.edit_message_text(
        "Подождите, идёт обработка",
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )


async def handle_back_or_cancel(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    if callback.data == "registration:cancel":
        await state.clear()
        await callback.message.edit_text("Регистрация отменена.")
    elif callback.data == "registration:back":
        current_state = await state.get_state()
        if current_state == UserRegistration.api_hash:
            await state.set_state(UserRegistration.api_id)
            await callback.message.edit_text(
                "🆔 Введите API ID 🆔",
                reply_markup=user.UserInlineButtons.back_and_cancel(
                    namespace="registration",
                ),
            )
        elif current_state == UserRegistration.phone:
            await state.set_state(UserRegistration.api_hash)
            await callback.message.edit_text(
                "🔑 Введите API Hash 🔑",
                reply_markup=user.UserInlineButtons.back_and_cancel(
                    namespace="registration",
                ),
            )
        elif current_state == UserRegistration.tg_code:
            await state.set_state(UserRegistration.password)
            await callback.message.edit_text(
                "🔐 Введите пароль 🔐",
                reply_markup=user.UserInlineButtons.back_and_cancel(
                    namespace="registration",
                ),
            )
    await callback.answer()
