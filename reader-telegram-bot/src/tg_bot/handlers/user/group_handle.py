import asyncpg
import structlog
from aiogram import types
from aiogram.fsm.context import FSMContext

from src.db.repositories import GroupThemeRepository
from src.tg_bot.keyboards.inline import callbacks
from src.tg_bot.keyboards.inline.user import HandleButtons, ThemeButtons
from src.user_bot.bot import UserClient


async def handle_command(
    msg: types.Message,
    user_clients: dict[int, UserClient],
) -> None:
    if msg.from_user is None:
        return

    client = user_clients.get(msg.from_user.id)
    groups = await client.get_active_groups()

    await msg.answer(
        "Выберите группу:",
        reply_markup=HandleButtons().groups_buttons(groups=groups),
    )


async def handle_theme_selection(
    cb: types.CallbackQuery,
    callback_data: callbacks.HandleGroupTheme,
    user_clients: dict[int, UserClient],
    state: FSMContext,
) -> None:
    if cb.from_user is None:
        return

    client = user_clients.get(cb.from_user.id)
    themes = await client.get_themes()

    # Отображение уже привязанных тем
    group_id = callback_data.group_id
    existing_themes = await client.get_themes_for_group(group_id)
    existing_themes = [theme.id for theme in existing_themes]

    await state.update_data(
        {
            "themes": themes,
            "existing_themes": existing_themes,
            "selected_themes": [],
        }
    )

    # Используем ThemeButtons для генерации клавиатуры с пагинацией
    keyboard = ThemeButtons.group_theme_selection(
        themes=themes,
        existing_themes=existing_themes,
        group_id=group_id,
    )

    await cb.message.edit_text(
        "Выберите темы для привязки или отвязки:", reply_markup=keyboard
    )
    await cb.answer()


async def paginate_themes(
    cb: types.CallbackQuery,
    callback_data: callbacks.HandleGroupTheme,
    state: FSMContext,
) -> None:

    data = await state.get_data()
    themes = data.get("themes", [])
    existing_themes = data.get("existing_themes", [])
    selected_themes = data.get("selected_themes", [])

    # Генерация клавиатуры для новой страницы
    keyboard = ThemeButtons.group_theme_selection(
        themes=themes,
        existing_themes=existing_themes,
        selected_themes=selected_themes,
        group_id=callback_data.group_id,
        page=callback_data.page,
        page_size=callback_data.page_size,
    )

    await cb.message.edit_reply_markup(reply_markup=keyboard)
    await cb.answer()


async def toggle_theme_selection(
    cb: types.CallbackQuery,
    callback_data: callbacks.HandleGroupTheme,
    state: FSMContext,
) -> None:

    data = await state.get_data()
    themes = data.get("themes", [])
    existing_themes = data.get("existing_themes", [])
    selected_themes = data.get("selected_themes", [])

    if callback_data.theme_id in selected_themes:
        selected_themes.remove(callback_data.theme_id)
    else:
        selected_themes.append(callback_data.theme_id)

    await state.update_data(selected_themes=selected_themes)

    keyboard = ThemeButtons.group_theme_selection(
        themes=themes,
        existing_themes=existing_themes,
        selected_themes=selected_themes,
        group_id=callback_data.group_id,
        page=callback_data.page,
        page_size=callback_data.page_size,
    )
    await cb.message.edit_reply_markup(reply_markup=keyboard)
    await cb.answer()


async def confirm_binding(
    cb: types.CallbackQuery,
    callback_data: callbacks.HandleGroupTheme,
    state: FSMContext,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
) -> None:
    
    data = await state.get_data()
    existing_themes = data.get("existing_themes", [])
    selected_themes = data.get("selected_themes", [])

    selected_set = set(selected_themes)
    existing_set = set(existing_themes)

    to_add = list(selected_set - existing_set)
    to_remove = list(selected_set & existing_set)

    repository = GroupThemeRepository(db_pool, db_logger)
    for theme_id in to_add:
        await repository.add_group_theme(
            callback_data.group_id, theme_id, cb.from_user.id
        )
    for theme_id in to_remove:
        await repository.remove_group_theme(
            callback_data.group_id, theme_id, cb.from_user.id
        )

    await cb.message.delete()
    await cb.message.answer("Темы успешно сохранены.")
    await state.clear()
