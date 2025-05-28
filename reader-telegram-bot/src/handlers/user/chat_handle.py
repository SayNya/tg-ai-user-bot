from aiogram import types
from aiogram.fsm.context import FSMContext
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories import ChatRepository, TopicRepository
from src.db.tables import ChatTopic
from src.keyboards.inline import callbacks
from src.keyboards.inline.user import HandleButtons, TopicButtons
from src.models.database import TopicDB


async def handle_command(
    msg: types.Message,
    chat_repository: ChatRepository,
) -> None:
    chats = await chat_repository.get_active_chats_by_user_id(user_id=msg.from_user.id)

    await msg.answer(
        "Выберите группу:",
        reply_markup=HandleButtons().chats_buttons(chats=chats),
    )


async def handle_topic_selection(
    cb: types.CallbackQuery,
    callback_data: callbacks.HandleChatTopic,
    state: FSMContext,
    topic_repository: TopicRepository,
) -> None:
    topics = await topic_repository.get_all_by_user_id(user_id=cb.from_user.id)
    topics_dict = [topic.model_dump() for topic in topics]
    # Отображение уже привязанных тем
    chat_id = callback_data.chat_id

    existing_topics = await topic_repository.get_all_by_user_id_and_chat_id(
        user_id=cb.from_user.id,
        chat_id=chat_id,
    )

    existing_topics = [topic.id for topic in existing_topics]

    await state.update_data(
        {
            "topics": topics_dict,
            "existing_topics": existing_topics,
            "selected_topics": [],
        },
    )

    # Используем TopicButtons для генерации клавиатуры с пагинацией
    keyboard = TopicButtons.chat_topic_selection(
        topics=topics,
        existing_topics=existing_topics,
        chat_id=chat_id,
    )

    await cb.message.edit_text(
        "Выберите темы для привязки или отвязки:",
        reply_markup=keyboard,
    )
    await cb.answer()


async def paginate_topics(
    cb: types.CallbackQuery,
    callback_data: callbacks.HandleChatTopic,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    topics = data.get("topics", [])
    existing_topics = data.get("existing_topics", [])
    selected_topics = data.get("selected_topics", [])

    # Генерация клавиатуры для новой страницы
    keyboard = TopicButtons.chat_topic_selection(
        topics=topics,
        existing_topics=existing_topics,
        selected_topics=selected_topics,
        chat_id=callback_data.chat_id,
        page=callback_data.page,
        page_size=callback_data.page_size,
    )

    await cb.message.edit_reply_markup(reply_markup=keyboard)
    await cb.answer()


async def toggle_topic_selection(
    cb: types.CallbackQuery,
    callback_data: callbacks.HandleChatTopic,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    topics = [TopicDB(**topic) for topic in data.get("topics", [])]
    existing_topics = data.get("existing_topics", [])
    selected_topics = data.get("selected_topics", [])

    if callback_data.topic_id in selected_topics:
        selected_topics.remove(callback_data.topic_id)
    else:
        selected_topics.append(callback_data.topic_id)

    await state.update_data(selected_topics=selected_topics)

    keyboard = TopicButtons.chat_topic_selection(
        topics=topics,
        existing_topics=existing_topics,
        selected_topics=selected_topics,
        chat_id=callback_data.chat_id,
        page=callback_data.page,
        page_size=callback_data.page_size,
    )
    await cb.message.edit_reply_markup(reply_markup=keyboard)
    await cb.answer()


async def confirm_binding(
    cb: types.CallbackQuery,
    callback_data: callbacks.HandleChatTopic,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    existing_topics = data.get("existing_topics", [])
    selected_topics = data.get("selected_topics", [])

    selected_set = set(selected_topics)
    existing_set = set(existing_topics)

    to_add = list(selected_set - existing_set)
    to_remove = list(selected_set & existing_set)

    session.add_all(to_add)
    session.execute(
        delete(ChatTopic).where(
            ChatTopic.chat_id == callback_data.chat_id,
            ChatTopic.topic_id.in_(to_remove),
        ),
    )
    await session.commit()

    await cb.message.delete()
    await cb.message.answer("Темы успешно сохранены.")
    await state.clear()
