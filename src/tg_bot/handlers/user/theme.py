import asyncpg
import structlog
from aiogram import Bot, types
from aiogram.fsm.context import FSMContext

from src.db.repositories import ThemeRepository
from src.tg_bot.keyboards.inline import user
from src.tg_bot.keyboards.inline.callbacks import (
    ThemeCallbackFactory,
    ThemeEditCallbackFactory,
    ThemeListCallbackFactory,
)
from src.tg_bot.states.user import ThemeEdit, UserTheme


async def themes_command(
    msg: types.Message,
) -> None:
    if msg.from_user is None:
        return

    m = "Выберите действие:"
    await msg.answer(m, reply_markup=user.theme.ThemeButtons().main())


# Добавление темы
async def add_theme(cb: types.CallbackQuery, state: FSMContext) -> None:
    if cb.from_user is None:
        return

    new_message = await cb.message.answer("Введите название темы:")
    await state.set_state(UserTheme.name)
    await state.update_data(msg_id=new_message.message_id)


async def name_theme(msg: types.Message, state: FSMContext, bot: Bot) -> None:
    if msg.from_user is None:
        return

    data = await state.get_data()
    await bot.delete_message(msg.chat.id, int(data["msg_id"]))

    new_message = await msg.answer("Введите описание темы:")
    await state.set_state(UserTheme.description)
    await state.update_data(msg_id=new_message.message_id, name=msg.text)


async def description_theme(msg: types.Message, state: FSMContext, bot: Bot) -> None:
    if msg.from_user is None:
        return

    data = await state.get_data()
    await bot.delete_message(msg.chat.id, int(data["msg_id"]))

    new_message = await msg.answer("Введите промпт для ответа на вопросы по этой теме:")
    await state.set_state(UserTheme.gpt)
    await state.update_data(msg_id=new_message.message_id, description=msg.text)


async def gpt_theme(
    msg: types.Message,
    state: FSMContext,
    bot: Bot,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
) -> None:
    if msg.from_user is None:
        return

    data = await state.get_data()
    await bot.delete_message(msg.chat.id, data["msg_id"])

    await ThemeRepository(db_pool, db_logger).create_theme(
        data["name"],
        data["description"],
        msg.text,
        msg.from_user.id,
    )

    await msg.answer("Тема сохранена")
    await state.clear()


# Редактирование темы
async def choose_theme_to_edit(
    cb: types.CallbackQuery,
    callback_data: ThemeCallbackFactory,
    state: FSMContext,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
) -> None:
    if cb.from_user is None:
        return

    themes = await ThemeRepository(db_pool, db_logger).get_themes_by_user_id(
        cb.from_user.id
    )
    page = callback_data.page
    reply_markup = user.theme.ThemeButtons().themes(themes, page)
    await cb.message.edit_text(
        "Выберите тему для редактирования:",
        reply_markup=reply_markup,
    )
    await cb.answer()


async def edit_theme(
    cb: types.CallbackQuery,
    callback_data: ThemeListCallbackFactory,
    state: FSMContext,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
) -> None:
    if cb.from_user is None:
        return

    theme = await ThemeRepository(db_pool, db_logger).get_theme_by_id(callback_data.id)
    if not theme:
        await cb.message.answer("Ошибка: тема не найдена.")
        return

    theme_details = (
        f"Название: {theme.name}\n"
        f"Описание: {theme.description}\n"
        f"Промпт: {theme.gpt}\n\n"
        "Выберите, что вы хотите изменить:"
    )

    max_length = 4096
    messages = [
        theme_details[i : i + max_length]
        for i in range(0, len(theme_details), max_length)
    ]

    for part in messages[:-1]:
        await cb.message.answer(part)

    new_message = await cb.message.answer(
        messages[-1], reply_markup=user.theme.ThemeButtons().edit_theme(theme)
    )
    await cb.message.delete()


async def delete_theme(
    cb: types.CallbackQuery,
    callback_data: ThemeEditCallbackFactory,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
) -> None:
    if cb.from_user is None:
        return

    await ThemeRepository(db_pool, db_logger).delete_theme(callback_data.id)
    await cb.message.answer("Тема успешно удалена.")
    await cb.message.delete()


async def input_theme_field_to_edit(
    cb: types.CallbackQuery,
    callback_data: ThemeEditCallbackFactory,
    state: FSMContext,
) -> None:
    if cb.from_user is None:
        return

    if callback_data.action == "edit_name":
        msg = "Введите новое название темы:"
        new_state = ThemeEdit.edit_name
    elif callback_data.action == "edit_description":
        msg = "Введите новое описание темы:"
        new_state = ThemeEdit.edit_description
    elif callback_data.action == "edit_prompt":
        new_state = ThemeEdit.edit_prompt
        msg = "Введите новый промпт для темы:"
    else:
        await cb.answer("Неизвестное действие.")
        return

    await cb.message.answer(msg)
    await state.set_state(new_state)

    await state.update_data(theme_id=callback_data.id)


async def edit_theme_field(
    msg: types.Message,
    state: FSMContext,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
) -> None:
    if msg.from_user is None:
        return

    data = await state.get_data()
    theme_id = data.get("theme_id")

    if not theme_id:
        await msg.answer("Ошибка: ID темы не найден.")
        return
    current_state = await state.get_state()
    if current_state == ThemeEdit.edit_name:
        await ThemeRepository(db_pool, db_logger).update_theme_field(
            theme_id, "name", msg.text
        )
        await msg.answer("Название темы успешно изменено.")
    elif current_state == ThemeEdit.edit_description:
        await ThemeRepository(db_pool, db_logger).update_theme_field(
            theme_id, "description", msg.text
        )
        await msg.answer("Описание темы успешно изменено.")
    elif current_state == ThemeEdit.edit_prompt:
        await ThemeRepository(db_pool, db_logger).update_theme_field(
            theme_id, "gpt", msg.text
        )
        await msg.answer("Промпт темы успешно изменен.")

    await state.clear()
