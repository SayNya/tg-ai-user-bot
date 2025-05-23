import structlog
from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telethon.errors import SessionPasswordNeededError

from src.db.tables import TelegramAuth
from src.models import TelegramAuthOut
from src.keyboards.inline.user import UserInlineButtons


async def start_restore(
    msg: types.Message,
    bot: Bot,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    user_id = msg.from_user.id
    user_client = user_clients.get(user_id)

    if user_client:
        await msg.answer("✅ Сессия уже активна.")
        return

    stmt = select(TelegramAuth).where(TelegramAuth.user_id == user_id)

    result = session.scalars(stmt).first()
    telegram_auth = TelegramAuthOut.model_validate(result)

    if not telegram_auth:
        await msg.answer(
            "❌ Нет данных для восстановления. Пожалуйста, зарегистрируйтесь заново с помощью /register.",
        )
        return

    user_client = UserClient(user_id=user_id, context=context, telegram_bot=bot)
    phone_code_hash = await user_client.init_client(
        api_id=telegram_auth.api_id,
        api_hash=telegram_auth.api_hash,
        phone=telegram_auth.phone,
    )

    await state.set_state("waiting_for_restore_code")
    await state.update_data(
        phone_code_hash=phone_code_hash,
        phone=telegram_auth.phone,
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
) -> None:
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
) -> None:
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
