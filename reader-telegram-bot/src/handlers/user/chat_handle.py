from aiogram import types
from aiogram.fsm.context import FSMContext
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import Chat, ChatTopic, Topic, User
from src.keyboards.inline import callbacks
from src.keyboards.inline.user import HandleButtons, TopicButtons
from src.models import ChatOut, TopicOut


async def handle_command(
    msg: types.Message,
    session: AsyncSession,
) -> None:
    stmt = select(User).where(
        User.telegram_user_id == msg.from_user.id,
    )
    res = await session.execute(stmt)
    user = res.scalars().one_or_none()
    stmt = select(Chat).where(
        Chat.user_id == user.id,
        Chat.is_active == True,
    )
    res = await session.execute(stmt)
    chats = [ChatOut(**chat) for chat in res.scalars().all()]

    await msg.answer(
        "Выберите группу:",
        reply_markup=HandleButtons().groups_buttons(chats=chats),
    )


async def handle_theme_selection(
    cb: types.CallbackQuery,
    callback_data: callbacks.HandleGroupTheme,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    stmt = select(User).where(
        User.telegram_user_id == cb.from_user.id,
    )
    res = await session.execute(stmt)
    user = res.scalars().one_or_none()

    stmt = select(Topic).where(
        Topic.user_id == user.id,
    )
    res = await session.execute(stmt)
    themes = [TopicOut(**topic) for topic in res.scalars().all()]

    # Отображение уже привязанных тем
    group_id = callback_data.group_id
    stmt = (
        select(Topic)
        .join(ChatTopic, Topic.id == ChatTopic.topic_id)
        .where(
            ChatTopic.chat_id == group_id,
            ChatTopic.user_id == user.id,
        )
    )
    res = await session.execute(stmt)
    existing_themes = [TopicOut(**topic) for topic in res.scalars().all()]
    existing_themes = [theme.id for theme in existing_themes]

    await state.update_data(
        {
            "themes": themes,
            "existing_themes": existing_themes,
            "selected_themes": [],
        },
    )

    # Используем ThemeButtons для генерации клавиатуры с пагинацией
    keyboard = TopicButtons.group_theme_selection(
        themes=themes,
        existing_themes=existing_themes,
        group_id=group_id,
    )

    await cb.message.edit_text(
        "Выберите темы для привязки или отвязки:",
        reply_markup=keyboard,
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
    keyboard = TopicButtons.group_theme_selection(
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

    keyboard = TopicButtons.group_theme_selection(
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
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    existing_themes = data.get("existing_themes", [])
    selected_themes = data.get("selected_themes", [])

    selected_set = set(selected_themes)
    existing_set = set(existing_themes)

    to_add = list(selected_set - existing_set)
    to_remove = list(selected_set & existing_set)

    session.add_all(to_add)
    session.execute(
        delete(ChatTopic).where(
            ChatTopic.chat_id == callback_data.group_id,
            ChatTopic.topic_id.in_(to_remove),
        ),
    )
    await session.commit()

    await cb.message.delete()
    await cb.message.answer("Темы успешно сохранены.")
    await state.clear()
