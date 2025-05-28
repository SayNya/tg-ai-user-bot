from aiogram import types
from aiogram.fsm.context import FSMContext

from src.db.repositories import ChatRepository, ChatTopicRepository, TopicRepository
from src.keyboards.inline import callbacks
from src.keyboards.inline.user import HandleButtons, TopicButtons
from src.models.database import TopicDB


async def handle_command(
    msg: types.Message,
    chat_repository: ChatRepository,
) -> None:
    """Handle the initial command to select a chat."""
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
    chat_topic_repository: ChatTopicRepository,
) -> None:
    """Handle the selection of topics for a chat."""
    # Get all user's topics
    topics = await topic_repository.get_all_by_user_id(user_id=cb.from_user.id)

    # Get currently bound topics for this chat
    bound_topic_ids = await chat_topic_repository.get_bound_topics(
        chat_id=callback_data.chat_id,
    )

    # Store data in state for later use
    await state.update_data(
        topics=[topic.model_dump() for topic in topics],
        bound_topic_ids=bound_topic_ids,
        selected_topic_ids=[],
        chat_id=callback_data.chat_id,
    )

    # Generate keyboard with pagination
    keyboard = TopicButtons.chat_topic_selection(
        topics=topics,
        bound_topic_ids=bound_topic_ids,
        selected_topic_ids=[],
        chat_id=callback_data.chat_id,
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
    """Handle topic list pagination."""
    data = await state.get_data()
    topics = [TopicDB(**topic) for topic in data["topics"]]
    bound_topic_ids = data["bound_topic_ids"]
    selected_topic_ids = data["selected_topic_ids"]

    keyboard = TopicButtons.chat_topic_selection(
        topics=topics,
        bound_topic_ids=bound_topic_ids,
        selected_topic_ids=selected_topic_ids,
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
    """Handle topic selection/deselection."""
    data = await state.get_data()
    topics = [TopicDB(**topic) for topic in data["topics"]]
    bound_topic_ids = data["bound_topic_ids"]
    selected_topic_ids = data["selected_topic_ids"]

    # If topic is currently bound, we want to unbind it
    # If topic is not bound, we want to bind it
    if callback_data.topic_id in bound_topic_ids:
        if callback_data.topic_id in selected_topic_ids:
            # Topic was bound and selected for unbinding, now deselect it
            selected_topic_ids.remove(callback_data.topic_id)
        else:
            # Topic was bound, now select it for unbinding
            selected_topic_ids.append(callback_data.topic_id)
    elif callback_data.topic_id in selected_topic_ids:
        # Topic was selected for binding, now deselect it
        selected_topic_ids.remove(callback_data.topic_id)
    else:
        # Topic was not bound, now select it for binding
        selected_topic_ids.append(callback_data.topic_id)

    await state.update_data(selected_topic_ids=selected_topic_ids)

    keyboard = TopicButtons.chat_topic_selection(
        topics=topics,
        bound_topic_ids=bound_topic_ids,
        selected_topic_ids=selected_topic_ids,
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
    chat_topic_repository: ChatTopicRepository,
) -> None:
    """Handle confirmation of topic binding changes."""
    data = await state.get_data()
    bound_topic_ids = data["bound_topic_ids"]
    selected_topic_ids = data["selected_topic_ids"]

    # Calculate which topics to add and remove
    # Topics to add: those that are selected but not currently bound
    to_add = list(set(selected_topic_ids) - set(bound_topic_ids))

    # Topics to remove: those that are currently bound but not selected
    to_remove = list(set(bound_topic_ids) - set(selected_topic_ids))

    # Apply changes
    if to_add:
        await chat_topic_repository.bind_topics(callback_data.chat_id, to_add)
    if to_remove:
        await chat_topic_repository.unbind_topics(callback_data.chat_id, to_remove)

    await cb.message.delete()
    await cb.message.answer("Темы успешно сохранены.")
    await state.clear()
