from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import Topic, User
from src.models.topic import TopicCreate, TopicOut
from src.tg_bot.keyboards.inline import user
from src.tg_bot.keyboards.inline.callbacks import (
    ThemeCallbackFactory,
    ThemeEditCallbackFactory,
    ThemeListCallbackFactory,
)
from src.tg_bot.states.user import ThemeEdit, UserTheme


async def themes_command(msg: types.Message, state: FSMContext) -> None:
    sent = await msg.answer(
        "📚 Выберите действие:",
        reply_markup=user.topic.TopicButtons().main(),
    )
    await state.update_data(working_message_id=sent.message_id)


# Добавление темы
async def add_theme(cb: types.CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    await bot.edit_message_text(
        "📝 Введите название темы:",
        chat_id=cb.message.chat.id,
        message_id=working_message_id,
    )
    await state.set_state(UserTheme.name)


async def name_theme(msg: types.Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    await msg.delete()
    await bot.edit_message_text(
        "🖋️ Введите описание темы:",
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )
    await state.set_state(UserTheme.description)
    await state.update_data(name=msg.text)


async def description_theme(msg: types.Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
    await bot.edit_message_text(
        "💡 Введите промпт темы:",
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )

    await state.set_state(UserTheme.gpt)
    await state.update_data(description=msg.text)


async def gpt_theme(
    msg: types.Message,
    state: FSMContext,
    bot: Bot,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    result = await session.execute(
        select(User).where(User.telegram_user_id == msg.from_user.id),
    )
    user = result.scalar_one_or_none()
    if not user:
        msg = f"User with telegram_user_id={msg.from_user.id} not found"
        raise ValueError(msg)

    new_topic = TopicCreate(
        name=data["name"],
        description=data["description"],
        prompt=msg.text,
        user_id=user.id,
    )
    topic = Topic(**new_topic.model_dump())
    session.add(topic)
    await session.commit()

    await msg.delete()
    await bot.edit_message_text(
        "✅ Тема успешно сохранена!",
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )

    await state.clear()


# Редактирование темы
async def choose_theme_to_edit(
    cb: types.CallbackQuery,
    callback_data: ThemeCallbackFactory,
    state: FSMContext,
    bot: Bot,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    stmt = (
        select(Topic)
        .join(User)
        .where(
            User.telegram_user_id == cb.from_user.id,
        )
    )
    result = await session.scalars(stmt)
    db_topics = result.all()
    topics = [TopicOut.model_validate(db_topic) for db_topic in db_topics]

    page = callback_data.page

    await bot.edit_message_text(
        "✅ Выберите тему для редактирования:",
        chat_id=cb.message.chat.id,
        message_id=working_message_id,
        reply_markup=user.topic.TopicButtons().topics(topics, page),
    )


async def edit_theme(
    cb: types.CallbackQuery,
    callback_data: ThemeListCallbackFactory,
    state: FSMContext,
    bot: Bot,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    stmt = select(Topic).where(Topic.id == callback_data.id)
    result = await session.scalars(stmt)
    topic_db = result.first()
    topic = TopicOut.model_validate(topic_db)

    if not topic:
        await cb.message.answer("Ошибка: тема не найдена.")
        return

    theme_details = (
        f"Название: {topic.name[:1000]}\n"
        f"Описание: {topic.description[:1000]}\n"
        f"Промпт: {topic.prompt[:1000]}\n\n"
        "Выберите, что вы хотите изменить:"
    )

    await bot.edit_message_text(
        theme_details,
        chat_id=cb.message.chat.id,
        message_id=working_message_id,
        reply_markup=user.topic.TopicButtons().edit_topic(topic),
    )


async def delete_theme(
    cb: types.CallbackQuery,
    callback_data: ThemeEditCallbackFactory,
    state: FSMContext,
    bot: Bot,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    stmt = delete(Topic).where(Topic.id == callback_data.id)
    await session.execute(stmt)
    await session.commit()

    await bot.edit_message_text(
        "🗑️ Тема успешно удалена.",
        chat_id=cb.message.chat.id,
        message_id=working_message_id,
    )


async def input_theme_field_to_edit(
    cb: types.CallbackQuery,
    callback_data: ThemeEditCallbackFactory,
    state: FSMContext,
    bot: Bot,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

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

    await bot.edit_message_text(
        msg,
        chat_id=cb.message.chat.id,
        message_id=working_message_id,
    )
    await state.set_state(new_state)

    await state.update_data(theme_id=callback_data.id)


async def edit_theme_field(
    msg: types.Message,
    state: FSMContext,
    bot: Bot,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    data = await state.get_data()
    theme_id = data.get("theme_id")

    if not theme_id:
        await msg.answer("Ошибка: ID темы не найден.")
        return
    current_state = await state.get_state()

    stmt = select(Topic).where(Topic.id == theme_id)
    result = await session.scalars(stmt)
    topic_db = result.first()

    if current_state == ThemeEdit.edit_name:
        topic_db.name = msg.text
        sent_msg = "✏️ Название темы успешно изменено."
    elif current_state == ThemeEdit.edit_description:
        topic_db.description = msg.text
        sent_msg = "📝 Описание темы успешно изменено."
    elif current_state == ThemeEdit.edit_prompt:
        topic_db.prompt = msg.text
        sent_msg = "💡 Промпт темы успешно изменен."

    await msg.delete()
    await bot.edit_message_text(
        sent_msg,
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )
    await session.commit()
    await state.clear()
