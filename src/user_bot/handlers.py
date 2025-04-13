from openai import AsyncOpenAI
from telethon import events
from telethon.tl.patched import Message

from src.user_bot.bot import UserClient


async def chat_handler(
    event: events.newmessage.NewMessage.Event,
    user_client: UserClient,
):
    logger = user_client.context["telethon_logger"]

    message_instance: Message = event.message
    message_text: str = message_instance.message
    sender_id = message_instance.sender_id

    mentioned_message_id = message_instance.reply_to_msg_id

    chat_id = event.chat_id

    openai_client: AsyncOpenAI = user_client.context["openai"]

    active_group_ids = await user_client.get_active_group_ids()

    if chat_id not in active_group_ids:
        return

    if sender_id == user_client.user_id:
        return

    if mentioned_message_id:
        mentioned_message = await user_client.get_mentioned_message(
            chat_id,
            mentioned_message_id,
            user_client.user_id,
        )
        if not mentioned_message:
            return
        messages = await user_client.get_messages_tree(mentioned_message_id)
        theme_id = messages[0].theme_id
        theme = await user_client.get_theme_by_id(theme_id)

        dialog_history = ""
        for message in messages:
            if message.sender_id == user_client.user_id:
                dialog_history += f"\nОтвет: {message.text}"
            else:
                dialog_history += f"\nСообщение клиента: {message.text}"
        dialog_history += f"\nСообщение клиента: {message_text}\nОтвет: <твой ответ>"

        system_prompt = f"Тебе необходимо сгенерировать ответ на сообщение клиента исходя из истории диалога. Ответ не должен содержать ссылок. Если в истории диалога ответов больше 5-и, то не отвечай на вопрос клиента, а предложи ему перейти в личные сообщения::Твоя роль: {theme.gpt}"

        prompt = f"История диалога: {dialog_history}"
        logger.debug("Диалог", prompt=prompt)
        answer = await chat_with_gpt(prompt, system_prompt, openai_client, logger)
        message_ans: Message = await message_instance.reply(answer)
        await user_client.add_message(
            msg_id=message_instance.id,
            text=message_text,
            chat_id=chat_id,
            sender_id=sender_id,
            theme_id=theme_id,
            mentioned_id=mentioned_message_id,
        )
        await user_client.add_message(
            msg_id=message_ans.id,
            text=answer,
            chat_id=chat_id,
            sender_id=user_client.user_id,
            theme_id=theme_id,
            mentioned_id=message_instance.id,
        )
        return

    # msg = await user_client.client_bot.send_message(
    #     -1002670657942, f"Принято сообщение:\n{message_text}"
    # )
    themes = await user_client.get_themes()
    if not themes:
        return
    system_prompt = 'Определи относится ли сообщение к одной из тем. Если относится напиши название темы. Если не относится ни к одной напиши "нет".\nТемы:'
    for theme in themes:
        system_prompt += (
            f"\nНазвание темы: {theme.name}\nОписание темы: {theme.description}::\n"
        )

    prompt = "Сообщение:\n" + message_text
    theme = await chat_with_gpt(prompt, system_prompt, openai_client, logger)

    # msg = await user_client.client_bot.send_message(
    #     -1002670657942, f"Бот определил тему:\n{theme}", reply_to=msg
    # )
    if theme == "нет":
        return

    theme = await user_client.get_theme_by_name(theme)

    system_prompt = theme.gpt
    prompt = message_text

    answer = await chat_with_gpt(prompt, system_prompt, openai_client, logger)

    # await user_client.client_bot.send_message(
    #     -1002670657942, f"Ответ бота:\n{answer_text}", reply_to=msg
    # )
    message_ans: Message = await message_instance.reply(answer)
    await user_client.add_message(
        msg_id=message_instance.id,
        text=message_text,
        chat_id=chat_id,
        sender_id=sender_id,
        theme_id=theme.id,
    )
    await user_client.add_message(
        msg_id=message_ans.id,
        text=answer,
        chat_id=chat_id,
        sender_id=user_client.user_id,
        theme_id=theme.id,
        mentioned_id=message_instance.id,
    )


async def private_handler(
    event: events.newmessage.NewMessage.Event,
    user_client: UserClient,
):

    logger = user_client.context["telethon_logger"]

    message_instance: Message = event.message
    message_text: str = message_instance.message
    sender_id = message_instance.sender_id

    if sender_id == user_client.user_id or sender_id == 7884058960:
        return

    chat_id = event.chat_id

    openai_client: AsyncOpenAI = user_client.context["openai"]

    history = await user_client.get_private_chat_history(chat_id)
    if not history:
        themes = await user_client.get_themes()
        system_prompt = 'Определи относится ли сообщение к одной из тем. Если относится напиши название темы. Если не относится ни к одной напиши "нет".\nТемы:'
        for theme in themes:
            system_prompt += (
                f"\nНазвание темы: {theme.name}\nОписание темы: {theme.description}::\n"
            )
        prompt = "Сообщение:\n" + message_text
        theme = await chat_with_gpt(prompt, system_prompt, openai_client, logger)
        if theme == "нет":
            return

        await user_client.chat_repository.add_chat(
            chat_id,
            "pr_name",
            user_client.user_id,
        )
        theme = await user_client.get_theme_by_name(theme)
        system_prompt = theme.gpt
        prompt = message_text

        answer = await chat_with_gpt(prompt, system_prompt, openai_client, logger)

        message_ans: Message = await message_instance.reply(answer)
        await user_client.add_message(
            msg_id=message_instance.id,
            text=message_text,
            chat_id=chat_id,
            sender_id=sender_id,
            theme_id=theme.id,
        )
        await user_client.add_message(
            msg_id=message_ans.id,
            text=answer,
            chat_id=chat_id,
            sender_id=user_client.user_id,
            theme_id=theme.id,
            mentioned_id=message_instance.id,
        )
        return

    theme = await user_client.get_theme_by_id(history[0].theme_id)

    dialog_history = ""
    for message in history:
        if message.sender_id == user_client.user_id:
            dialog_history += f"\nОтвет: {message.text}"
        else:
            dialog_history += f"\nСообщение клиента: {message.text}"
    dialog_history += f"\nСообщение клиента: {message_text}\nОтвет: <твой ответ>"

    system_prompt = f"Тебе необходимо сгенерировать ответ на сообщение клиента исходя из истории диалога. Ответ может содержать ссылок.::Твоя роль: {theme.gpt}"

    prompt = f"История диалога: {dialog_history}"

    answer = await chat_with_gpt(prompt, system_prompt, openai_client, logger)
    message_ans: Message = await message_instance.reply(answer)
    await user_client.add_message(
        msg_id=message_instance.id,
        text=message_text,
        chat_id=chat_id,
        sender_id=sender_id,
        theme_id=theme.id,
        mentioned_id=history[-1].id,
    )
    await user_client.add_message(
        msg_id=message_ans.id,
        text=answer,
        chat_id=chat_id,
        sender_id=user_client.user_id,
        theme_id=theme.id,
        mentioned_id=message_instance.id,
    )


async def chat_with_gpt(
    prompt: str,
    system_prompt: str,
    client: AsyncOpenAI,
    logger,
    model: str = "gpt-4o-mini",
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
        logger.debug("Got GPT response", response=response)
        return response.choices[0].message.content
    except Exception as e:
        raise e
