from datetime import datetime, timedelta
from openai import AsyncOpenAI
import pytz
from telethon import events
from telethon.tl.patched import Message

from src.data import config
from src.user_bot.bot import UserClient


async def chat_with_gpt(
    prompt: str,
    system_prompt: str,
    client: AsyncOpenAI,
    logger,
    model: str = "deepseek-chat",
) -> str:
    try:
        logger.debug("Making GPT request")
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        logger.debug("Got GPT response", response_id=response.id, message=response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        logger.error("Exception occurred while making GPT request", exc_info=True)
        raise e


async def build_dialog_history(messages, user_id, latest_text):
    history = ""
    for message in messages:
        role = "Ответ" if message.sender_id == user_id else "Сообщение клиента"
        history += f"\n{role}: {message.text}"
    return f"{history}\nСообщение клиента: {latest_text}\nОтвет: <твой ответ>"


async def handle_gpt_response(prompt, system_prompt, openai_client, logger):
    logger.debug("Диалог", prompt=prompt)
    return await chat_with_gpt(prompt, system_prompt, openai_client, logger)


async def reply_and_store(message_instance, answer, user_client, chat_id, sender_id, theme_id, sender_username=None, mentioned_id=None):
    message_ans = await message_instance.reply(answer)
    await user_client.add_message(
        msg_id=message_instance.id,
        text=message_instance.message,
        chat_id=chat_id,
        sender_id=sender_id,
        theme_id=theme_id,
        mentioned_id=mentioned_id,
        sender_username=sender_username,
    )
    await user_client.add_message(
        msg_id=message_ans.id,
        text=answer,
        chat_id=chat_id,
        sender_id=user_client.user_id,
        theme_id=theme_id,
        mentioned_id=message_instance.id,
    )


async def chat_handler(event: events.newmessage.NewMessage.Event, user_client: UserClient):
    logger = user_client.context["telethon_logger"]
    message_instance: Message = event.message
    message_text: str = message_instance.message
    sender_id = message_instance.sender_id
    chat_id = event.chat_id
    openai_client: AsyncOpenAI = user_client.context["openai"]

    if sender_id == user_client.user_id:
        return

    active_group_ids = await user_client.get_active_group_ids()
    if chat_id not in active_group_ids:
        return

    mentioned_message_id = message_instance.reply_to_msg_id
    sender = await message_instance.get_sender()
    sender_username = sender.username if sender else None

    if mentioned_message_id:
        mentioned_message = await user_client.get_mentioned_message(chat_id, mentioned_message_id, user_client.user_id)
        if not mentioned_message:
            return
        messages = await user_client.get_messages_tree(mentioned_message_id)
        theme_id = messages[0].theme_id
        theme = await user_client.get_theme_by_id(theme_id)
        dialog_history = await build_dialog_history(messages, user_client.user_id, message_text)
        system_prompt = f"Тебе необходимо сгенерировать ответ на сообщение клиента исходя из истории диалога. Ответ не должен содержать ссылок.::Твоя роль: {theme.gpt}"
        answer = await handle_gpt_response(f"История диалога: {dialog_history}", system_prompt, openai_client, logger)
        await reply_and_store(message_instance, answer, user_client, chat_id, sender_id, theme_id, sender_username, mentioned_message_id)
        return

    recent_message = await user_client.get_message_by_chat_and_sender(chat_id, sender_id)
    if recent_message and recent_message.created_at.replace(tzinfo=pytz.UTC) >= datetime.now(pytz.UTC) - timedelta(minutes=30):
        root_message = await user_client.get_message_by_mentioned_id(recent_message.id)
        messages = await user_client.get_messages_tree(root_message.id)
        theme_id = messages[0].theme_id
        theme = await user_client.get_theme_by_id(theme_id)
        dialog_history = await build_dialog_history(messages, user_client.user_id, message_text)
        system_prompt = f"Тебе необходимо сгенерировать ответ на сообщение клиента исходя из истории диалога. Ответ не должен содержать ссылок.::Твоя роль: {theme.gpt}"
        answer = await handle_gpt_response(f"История диалога: {dialog_history}", system_prompt, openai_client, logger)
        await reply_and_store(message_instance, answer, user_client, chat_id, sender_id, theme_id, sender_username, root_message.id)
        return

    themes = await user_client.get_themes()
    if not themes:
        return
    system_prompt = 'Определи относится ли сообщение к одной из тем. Если относится напиши только название темы. Если не относится ни к одной напиши "нет".\nТемы:'
    for theme in themes:
        system_prompt += f"\nНазвание темы: {theme.name}\nОписание темы: {theme.description}::\n"
    theme_name = await chat_with_gpt("Сообщение:\n" + message_text, system_prompt, openai_client, logger)
    if theme_name == "нет":
        return
    theme = await user_client.get_theme_by_name(theme_name)
    answer = await chat_with_gpt(message_text, theme.gpt, openai_client, logger)
    await reply_and_store(message_instance, answer, user_client, chat_id, sender_id, theme.id, sender_username)


async def private_handler(event: events.newmessage.NewMessage.Event, user_client: UserClient):
    logger = user_client.context["telethon_logger"]
    message_instance: Message = event.message
    message_text: str = message_instance.message
    sender_id = message_instance.sender_id
    chat_id = event.chat_id

    if sender_id in [user_client.user_id, config.BOT_ID]:
        return

    openai_client: AsyncOpenAI = user_client.context["openai"]
    history = await user_client.get_private_chat_history(chat_id)
    sender = await message_instance.get_sender()
    sender_username = sender.username if sender else None

    if not history:
        themes = await user_client.get_themes()
        system_prompt = 'Определи относится ли сообщение к одной из тем. Если относится напиши только название темы. Если не относится ни к одной напиши "нет".\nТемы:'
        for theme in themes:
            system_prompt += f"\nНазвание темы: {theme.name}\nОписание темы: {theme.description}::\n"
        theme_name = await chat_with_gpt("Сообщение:\n" + message_text, system_prompt, openai_client, logger)
        if theme_name == "нет":
            return
        theme = await user_client.get_theme_by_name(theme_name)
        answer = await chat_with_gpt(message_text, theme.gpt, openai_client, logger)
        await reply_and_store(message_instance, answer, user_client, chat_id, sender_id, theme.id, sender_username)
        return

    theme = await user_client.get_theme_by_id(history[0].theme_id)
    dialog_history = await build_dialog_history(history, user_client.user_id, message_text)
    system_prompt = f"Тебе необходимо сгенерировать ответ на сообщение клиента исходя из истории диалога. Ответ может содержать ссылок.::Твоя роль: {theme.gpt}"
    answer = await handle_gpt_response(f"История диалога: {dialog_history}", system_prompt, openai_client, logger)
    await reply_and_store(message_instance, answer, user_client, chat_id, sender_id, theme.id, sender_username, history[-1].id)
