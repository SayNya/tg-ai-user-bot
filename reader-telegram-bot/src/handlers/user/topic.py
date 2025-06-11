from aiogram import Bot, types
from aiogram.fsm.context import FSMContext

from src.db.repositories import (
    ChatRepository,
    TopicRepository,
)
from src.enums import RabbitMQQueuePublisher
from src.exceptions import DatabaseNotFoundError
from src.keyboards.inline import user
from src.keyboards.inline.callbacks import (
    TopicCallbackFactory,
    TopicEditCallbackFactory,
    TopicListCallbackFactory,
)
from src.models.database import TopicCreateDB
from src.rabbitmq.publisher import RabbitMQPublisher
from src.states.user import TopicEdit, UserTopic


async def topics_command(msg: types.Message, state: FSMContext) -> None:
    sent = await msg.answer(
        "📚 Выберите действие:",
        reply_markup=user.topic.TopicButtons().main(),
    )
    await state.update_data(working_message_id=sent.message_id)


async def add_topic(cb: types.CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    await bot.edit_message_text(
        "📝 Введите название темы:",
        chat_id=cb.message.chat.id,
        message_id=working_message_id,
    )
    await state.set_state(UserTopic.name)


async def name_topic(msg: types.Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    await msg.delete()
    await bot.edit_message_text(
        "🖋️ Введите описание темы:",
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )
    await state.set_state(UserTopic.description)
    await state.update_data(name=msg.text)


async def description_topic(msg: types.Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
    await bot.edit_message_text(
        "💡 Введите промпт темы:",
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )

    await state.set_state(UserTopic.gpt)
    await state.update_data(description=msg.text)


async def gpt_topic(
    msg: types.Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
    await bot.edit_message_text(
        "💡 Введите ключевые слова темы через запятую:",
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )

    await state.set_state(UserTopic.keywords)
    await state.update_data(prompt=msg.text)


async def keywords_topic(
    msg: types.Message,
    state: FSMContext,
    bot: Bot,
    topic_repository: TopicRepository,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    keywords = msg.text.split(",")
    new_topic = TopicCreateDB(
        name=data.get("name"),
        description=data.get("description"),
        prompt=data.get("prompt"),
        keywords=keywords,
        user_id=msg.from_user.id,
    )
    await topic_repository.create(new_topic)

    await msg.delete()
    await bot.edit_message_text(
        "✅ Тема успешно сохранена!",
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )

    await state.clear()


async def choose_topic_to_edit(
    cb: types.CallbackQuery,
    callback_data: TopicCallbackFactory,
    state: FSMContext,
    bot: Bot,
    topic_repository: TopicRepository,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    topics = await topic_repository.get_all_by_user_id(cb.from_user.id)

    page = callback_data.page

    await bot.edit_message_text(
        "✅ Выберите тему для редактирования:",
        chat_id=cb.message.chat.id,
        message_id=working_message_id,
        reply_markup=user.topic.TopicButtons().topics(topics, page),
    )


async def edit_topic(
    cb: types.CallbackQuery,
    callback_data: TopicListCallbackFactory,
    state: FSMContext,
    bot: Bot,
    topic_repository: TopicRepository,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    try:
        topic = await topic_repository.get(callback_data.id)
    except DatabaseNotFoundError:
        await bot.edit_message_text(
            "Ошибка: тема не найдена.",
            chat_id=cb.message.chat.id,
            message_id=working_message_id,
        )
        return

    topic_details = (
        f"📝 *Информация о теме*\n\n"
        f"*Название:*\n{topic.name[:1000]}\n\n"
        f"*Описание:*\n{topic.description[:1000]}\n\n"
        f"*Промпт:*\n{topic.prompt[:1000]}\n\n"
        f"*Ключевые слова:*\n{', '.join(topic.keywords) if topic.keywords else 'Не указаны'}\n\n"
        "Выберите, что вы хотите изменить:"
    )

    await bot.edit_message_text(
        topic_details,
        chat_id=cb.message.chat.id,
        message_id=working_message_id,
        reply_markup=user.topic.TopicButtons().edit_topic(topic),
        parse_mode="Markdown",
    )


async def delete_topic(
    cb: types.CallbackQuery,
    callback_data: TopicEditCallbackFactory,
    state: FSMContext,
    bot: Bot,
    chat_repository: ChatRepository,
    topic_repository: TopicRepository,
    publisher: RabbitMQPublisher,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    # Get topic before deletion to get user_id
    topic = await topic_repository.get(callback_data.id)
    await topic_repository.delete(callback_data.id)

    # Invalidate cache for all chats where this topic was used
    bound_chats = await chat_repository.get_chats_by_topic_id(callback_data.id)
    for chat in bound_chats:
        await publisher.publish(
            payload={
                "user_id": topic.user_id,
                "chat_id": chat.id,
            },
            routing_key=RabbitMQQueuePublisher.SERVER_CACHE_INVALIDATION,
        )

    await bot.edit_message_text(
        "🗑️ Тема успешно удалена.",
        chat_id=cb.message.chat.id,
        message_id=working_message_id,
    )


async def input_topic_field_to_edit(
    cb: types.CallbackQuery,
    callback_data: TopicEditCallbackFactory,
    state: FSMContext,
    bot: Bot,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")

    if callback_data.action == "edit_name":
        msg = "Введите новое название темы:"
        new_state = TopicEdit.edit_name
    elif callback_data.action == "edit_description":
        msg = "Введите новое описание темы:"
        new_state = TopicEdit.edit_description
    elif callback_data.action == "edit_prompt":
        new_state = TopicEdit.edit_prompt
        msg = "Введите новый промпт для темы:"
    elif callback_data.action == "edit_prompt":
        new_state = TopicEdit.edit_keywords
        msg = "Введите ключевые слова черех запятую:"
    else:
        await cb.answer("Неизвестное действие.")
        return

    await bot.edit_message_text(
        msg,
        chat_id=cb.message.chat.id,
        message_id=working_message_id,
    )
    await state.set_state(new_state)

    await state.update_data(topic_id=callback_data.id)


async def edit_topic_field(
    msg: types.Message,
    state: FSMContext,
    bot: Bot,
    chat_repository: ChatRepository,
    topic_repository: TopicRepository,
    publisher: RabbitMQPublisher,
) -> None:
    data = await state.get_data()
    working_message_id = data.get("working_message_id")
    topic_id = data.get("topic_id")

    if not topic_id:
        await msg.answer("Ошибка: ID темы не найден.")
        return
    current_state = await state.get_state()

    try:
        if current_state == TopicEdit.edit_name:
            await topic_repository.update_name(topic_id, msg.text)
            sent_msg = "✏️ Название темы успешно изменено."
        elif current_state == TopicEdit.edit_description:
            await topic_repository.update_description(topic_id, msg.text)
            sent_msg = "📝 Описание темы успешно изменено."
        elif current_state == TopicEdit.edit_prompt:
            await topic_repository.update_prompt(topic_id, msg.text)
            sent_msg = "💡 Промпт темы успешно изменен."
        elif current_state == TopicEdit.edit_keywords:
            keywords = msg.text.split(",")
            await topic_repository.update_keywords(topic_id, keywords)
            sent_msg = "💡 Ключевые слова темы успешно изменены."

        bound_chats = await chat_repository.get_chats_by_topic_id(topic_id)
        for chat in bound_chats:
            await publisher.publish(
                payload={
                    "user_id": msg.from_user.id,
                    "chat_id": chat.id,
                },
                routing_key=RabbitMQQueuePublisher.SERVER_CACHE_INVALIDATION,
            )

    except DatabaseNotFoundError:
        sent_msg = "Изменения не сохранены, так как тема не найдена."

    await msg.delete()
    await bot.edit_message_text(
        sent_msg,
        chat_id=msg.chat.id,
        message_id=working_message_id,
    )
    await state.clear()
