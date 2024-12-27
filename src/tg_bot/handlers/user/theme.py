import asyncpg
import structlog
from aiogram import types, Bot
from aiogram.fsm.context import FSMContext

from src.db.repositories import ThemeRepository
from src.tg_bot.keyboards.inline import user
from src.tg_bot.states.user import UserTheme
from src.user_bot.utils import UserBot


async def themes_command(
    msg: types.Message,
):
    if msg.from_user is None:
        return

    m = "Выберите действие:"
    await msg.answer(m, reply_markup=user.group.GroupButtons().main())


async def start_theme(msg: types.Message, state: FSMContext):
    if msg.from_user is None:
        return

    new_message = await msg.answer("Введите название темы:")
    await state.set_state(UserTheme.name)
    await state.update_data(msg_id=new_message.message_id)


async def name_theme(msg: types.Message, state: FSMContext, bot: Bot):
    if msg.from_user is None:
        return

    data = await state.get_data()
    await bot.delete_message(msg.chat.id, int(data["msg_id"]))
    await msg.delete()

    new_message = await msg.answer("Введите описание темы:")
    await state.set_state(UserTheme.description)
    await state.update_data(msg_id=new_message.message_id, name=msg.text)


async def description_theme(
    msg: types.Message,
    state: FSMContext,
    bot: Bot,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
):
    if msg.from_user is None:
        return

    data = await state.get_data()
    await bot.delete_message(msg.chat.id, data["msg_id"])
    await msg.delete()

    await ThemeRepository(db_pool, db_logger).create_theme(
        data["name"], msg.text, msg.from_user.id
    )

    await msg.answer("Тема сохранена")
    await state.clear()
