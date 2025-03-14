from aiogram import types
from aiogram.fsm.context import FSMContext
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from src import utils
from src.tg_bot.keyboards.default import BasicButtons
from src.tg_bot.states.user import UserRegistration
from src.user_bot.bot import UserClient


async def start_registration(
    msg: types.Message,
    state: FSMContext,
    user_clients: dict[int, TelegramClient],
) -> None:
    if msg.from_user is None:
        return

    client = user_clients.get(msg.from_user.id)
    if client is not None:
        await msg.answer("Вы уже зарегистрированы")
        return

    await state.set_state(UserRegistration.api_id)

    sent_message = await msg.answer("🆔 Введите API ID 🆔")
    await state.update_data(previous_bot_message_id=sent_message.message_id)


async def api_id_registration(
    msg: types.Message,
    state: FSMContext,
) -> None:
    if msg.from_user is None or msg.text is None:
        return

    await utils.messages.delete_message(msg, previous_bot=True, state=state)

    try:
        api_id = int(msg.text)
    except ValueError:
        await msg.answer("⚠️ API ID должен быть числом ⚠️")
        return

    await state.update_data(api_id=api_id)
    await state.set_state(UserRegistration.api_hash)

    sent_message = await msg.answer("🔑 Введите API Hash 🔑")
    await state.update_data(previous_bot_message_id=sent_message.message_id)


async def api_hash_registration(
    msg: types.Message,
    state: FSMContext,
) -> None:
    if msg.from_user is None:
        return

    await utils.messages.delete_message(msg, previous_bot=True, state=state)

    await state.update_data(api_hash=msg.text)
    await state.set_state(UserRegistration.phone)

    sent_message = await msg.answer("📱 Введите номер телефона 📱")
    await state.update_data(previous_bot_message_id=sent_message.message_id)


async def phone_registration(
    msg: types.Message,
    state: FSMContext,
) -> None:
    if msg.from_user is None:
        return

    await utils.messages.delete_message(msg, previous_bot=True, state=state)

    await state.update_data(phone=msg.text)
    await state.set_state(UserRegistration.have_password)

    sent_message = await msg.answer(
        "🔑 У вас есть пароль от аккаунта? 🔑",
        reply_markup=BasicButtons.yes_n_no(),
    )
    await state.update_data(previous_bot_message_id=sent_message.message_id)


async def have_password(
    msg: types.Message,
    state: FSMContext,
) -> None:
    if msg.from_user is None:
        return

    await utils.messages.delete_message(msg, previous_bot=True, state=state)

    await state.set_state(UserRegistration.password)

    sent_message = await msg.answer("🔐 Введите пароль 🔐")
    await state.update_data(previous_bot_message_id=sent_message.message_id)


async def password_registration(
    msg: types.Message,
    state: FSMContext,
    user_clients: dict[int, UserClient],
    context: utils.shared_context.AppContext,
) -> None:
    if msg.from_user is None:
        return

    await utils.messages.delete_message(msg, previous_bot=True, state=state)

    await state.update_data(password=msg.text)
    await register_client(msg, state, user_clients, context)


async def register_client(
    msg: types.Message,
    state: FSMContext,
    user_clients: dict[int, UserClient],
    context: utils.shared_context.AppContext,
) -> None:
    if msg.from_user is None or msg.bot is None:
        return

    data = await state.get_data()
    user_id = msg.from_user.id
    user_bot = UserClient(
        user_id=user_id,
        context=context,
        telegram_bot=msg.bot,
    )
    phone_code_hash = await user_bot.init_client(
        api_id=data["api_id"],
        api_hash=data["api_hash"],
        phone=data["phone"],
    )

    sent_message = await msg.answer(
        """🔹 Введите код подтверждения 🔹

Пожалуйста, укажите код, который пришел вам в Telegram, в формате:
📌 "123_45"

❗ Обратите внимание на нижнее подчеркивание между числами!""",
    )
    await state.update_data(
        phone_code_hash=phone_code_hash, previous_bot_message_id=sent_message.message_id
    )
    await state.set_state(UserRegistration.tg_code)
    user_clients[user_id] = user_bot


async def tg_code_registration(
    msg: types.Message,
    state: FSMContext,
    user_clients: dict[int, UserClient],
) -> None:
    if msg.from_user is None or msg.text is None:
        return

    await utils.messages.delete_message(msg, previous_bot=True, state=state)

    data = await state.get_data()
    user_id = msg.from_user.id
    user_bot = user_clients.get(user_id)
    if user_bot is None:
        return

    tg_code = msg.text.split("_")
    if len(tg_code) != 2:
        await msg.answer("Неверный формат кода")
        return
    tg_code = "".join(tg_code)

    try:
        await user_bot.confirm_code(
            phone=data["phone"],
            code=tg_code,
            phone_code_hash=data["phone_code_hash"],
        )
    except SessionPasswordNeededError:
        password = data.get("password")
        if password is None:
            await msg.answer("Введите пароль:")
            await state.set_state(UserRegistration.password)
            return
        await user_bot.enter_password(password)

    await user_bot.add_credentials(data["api_id"], data["api_hash"], data["phone"])
    await msg.answer("✅ Регистрация успешно завершена! ✅")
    await state.clear()
