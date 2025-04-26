import structlog
from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from telethon.errors import SessionPasswordNeededError

from src.context import AppContext
from src.db.repositories.credentials import CredentialsRepository
from src.models.credentials import CredentialsModel
from src.tg_bot.keyboards.inline.user import UserInlineButtons
from src.user_bot.bot import UserClient


async def start_restore(
    msg: types.Message,
    bot: Bot,
    state: FSMContext,
    user_clients: dict[int, UserClient],
    context: AppContext,
) -> None:
    if msg.from_user is None:
        return

    user_id = msg.from_user.id
    user_client = user_clients.get(user_id)

    if user_client:
        await msg.answer("✅ Сессия уже активна.")
        return

    cd_repository = CredentialsRepository(
        context["db_pool"],
        context["db_logger"],
    )
    credentials: CredentialsModel | None = (
        await cd_repository.get_credentials_by_user_id(user_id)
    )
    if not credentials:
        await msg.answer(
            "❌ Нет данных для восстановления. Пожалуйста, зарегистрируйтесь заново с помощью /register."
        )
        return

    user_client = UserClient(user_id=user_id, context=context, telegram_bot=bot)
    phone_code_hash = await user_client.init_client(
        api_id=credentials.api_id,
        api_hash=credentials.api_hash,
        phone=credentials.phone,
    )

    await state.set_state("waiting_for_restore_code")
    await state.update_data(
        phone_code_hash=phone_code_hash,
        phone=credentials.phone,
        user_client=user_client,
    )

    await msg.answer(
        "🔹 Введите код подтверждения 🔹\n\n"
        'Пожалуйста, укажите код, который пришел вам в Telegram, в формате:📌 "123_45"\n\n'
        "❗ Обратите внимание на нижнее подчеркивание между числами!",
        reply_markup=UserInlineButtons.cancel(namespace="restore"),
    )


async def restore_code(
    msg: types.Message,
    state: FSMContext,
    user_clients: dict[int, UserClient],
) -> None:
    if msg.from_user is None or msg.text is None:
        return

    data = await state.get_data()
    phone_code_hash = data.get("phone_code_hash")
    phone = data.get("phone")
    user_client = data.get("user_client")

    if not phone_code_hash or not phone:
        await msg.answer("❌ Ошибка восстановления сессии. Попробуйте заново.")
        return

    user_id = msg.from_user.id

    tg_code = msg.text.split("_")
    if len(tg_code) != 2:
        await msg.answer("Неверный формат кода")
        return
    tg_code = "".join(tg_code)

    try:
        await user_client.confirm_code(
            phone=phone,
            code=tg_code,
            phone_code_hash=phone_code_hash,
        )
        await msg.answer("✅ Сессия успешно восстановлена!")
        user_clients[user_id] = user_client
        await state.clear()
    except SessionPasswordNeededError:
        await msg.answer(
            "🔐 Введите пароль для восстановления сессии:",
            reply_markup=UserInlineButtons.cancel(namespace="restore"),
        )
        await state.set_state("waiting_for_restore_password")
    except Exception as e:
        logger = structlog.get_logger()
        logger.error("Ошибка при подтверждении кода", error=str(e))
        await msg.answer("❌ Неверный код подтверждения. Попробуйте снова.")


async def restore_password(
    msg: types.Message,
    state: FSMContext,
    user_clients: dict[int, UserClient],
) -> None:
    if msg.from_user is None or msg.text is None:
        return

    user_id = msg.from_user.id
    data = await state.get_data()
    user_client: UserClient = data.get("user_client")

    if not user_client:
        await msg.answer("❌ Клиент не найден. Пожалуйста, зарегистрируйтесь заново.")
        return

    try:
        await user_client.enter_password(msg.text)
        await msg.answer("✅ Сессия успешно восстановлена!")
        user_clients[user_id] = user_client
        await state.clear()
    except Exception as e:
        logger = structlog.get_logger()
        logger.error("Ошибка при вводе пароля", error=str(e))
        await msg.answer("❌ Неверный пароль. Попробуйте снова.")
