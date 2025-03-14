from openai import AsyncOpenAI
from telethon import events
from telethon.tl.types import User, Channel
from telethon.tl.patched import Message

from src.user_bot.bot import UserClient


async def message_handler(event: events.newmessage.NewMessage.Event, user_client: UserClient):
    logger = user_client.context["telethon_logger"]
    chat_id = event.chat_id
    active_group_ids = await user_client.get_active_group_ids()
    logger.debug("Chat ids", active_group_ids=active_group_ids, chat_id=chat_id)
    if chat_id not in active_group_ids:
        return

    message_instance: Message = event.message

    logger.debug("Message instance", message_instance=type(message_instance))
    logger.debug("Sender ids", sender_id=message_instance.sender_id, user_id=user_client.user_id)
    if message_instance.sender_id == user_client.user_id:
        return

    # logger.debug("Sender instance", sender_type=type(event.sender))
    # if not (isinstance(event.sender, User) or isinstance(event.sender, Channel)):
    #     return

    openai_client: AsyncOpenAI = user_client.context["openai"]

    message_text: str = message_instance.message
    msg = await user_client.client_bot.send_message(-1002670657942, f"Принято сообщение:\n{message_text}")
    themes = await user_client.get_themes()
    system_prompt = "Определи относится ли сообщение к одной из тем. Если относится напиши название темы. Если не относится ни к одной напиши \"нет\".\nТемы:"
    for theme in themes:
        system_prompt += f"\nНазвание темы: {theme.name}\nОписание темы: {theme.description}::\n"

    prompt = "Сообщение:\n" + message_text
    theme = await chat_with_gpt(prompt, system_prompt, openai_client, logger)

    msg = await user_client.client_bot.send_message(-1002670657942, f"Бот определил тему:\n{theme}", reply_to=msg)
    if theme == "нет":
        return

    theme = await user_client.get_theme_by_name(theme)

    mentioned: bool = message_instance.mentioned
    mentioned_message_id = message_instance.reply_to_msg_id if mentioned else -1

    sender_id = str(message_instance.sender_id)

    system_prompt = theme.gpt
    prompt = message_text

    answer_text = await chat_with_gpt(prompt, system_prompt, openai_client, logger)

    await user_client.client_bot.send_message(-1002670657942, f"Ответ бота:\n{answer_text}", reply_to=msg)
    message = await message_instance.reply(answer_text)
    #
    # sender = event.get_sender()
    #
    # new_message_id = await user_client.add_message(
    #                 message_id=message_instance.id,
    #                 sender_id=sender_id,
    #                 theme_name=list(themes.keys())[0],
    #                 username=sender.username,
    #                 message=message_text,
    #                 chat_unique_id=chat_id,
    #                 mentioned_message_id=mentioned_message_id,
    #             )
    # if mentioned:
    #     log.info('mentioned')
    #     for user_id in trigger_data:
    #         themes = trigger_data[user_id].get(str(chat_id))
    #         if themes:
    #             user_spam = generic_spams.get(user_id)
    #             if user_spam and message_text in user_spam:
    #                 continue
    #             new_message_id = db_add_message(
    #                 message_id=message_instance.id,
    #                 sender_id=sender_id,
    #                 theme_name=list(themes.keys())[0],
    #                 username=username,
    #                 message=message_text,
    #                 chat_unique_id=str(chat_id),
    #                 user_id=user_id,
    #                 mentioned_message_id=mentioned_message_id,
    #             )
    #             sender = await event.get_sender()
    #             await event.client.get_input_entity(sender)
    #             # db_add_user_message(chat_id=..., user_id=..., message=...)
    #             reply_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    #                 [InlineKeyboardButton(text='Сформировать сообщение от конструктора',
    #                                       callback_data=f'incoming_message:answer:{new_message_id}')],
    #                 [InlineKeyboardButton(text='Написать собственный ответ',
    #                                       callback_data=f'incoming_message:custom_message:{new_message_id}')],
    #                 [InlineKeyboardButton(text='Добавить в спам',
    #                                       callback_data=f'incoming_message:spam:{new_message_id}')],
    #                 [InlineKeyboardButton(text='Пропустить', callback_data=f'incoming_message:skip:{new_message_id}')],
    #             ])
    #
    #             log.info(msg=f'Send notification to user {user_id}')
    #             message = await bot.send_message(
    #                 chat_id=user_id,
    #                 text=f'Есть упоминание вас в чате: t.me/{message_instance.chat.username}/{message_instance.id}\nТекст сообщения: {message_text}',
    #                 reply_markup=reply_keyboard
    #             )
    #             message_id = message.message_id
    #             db_add_user_message(chat_id=BOT_ID, user_id=user_id, message_id=message_id, message=message_text)
    #             break
    #     return 0
    # for user in trigger_data:
    #     themes = trigger_data[user].get(str(chat_id))
    #
    #     user_spam = generic_spams.get(user)
    #     if user_spam and message_text in user_spam:
    #         continue
    #     if themes:
    #         for theme in themes:
    #             triggers_true = False
    #             for word in themes[theme]['triggers']:
    #                 if word in text:
    #                     triggers_true = True
    #                     break
    #             if triggers_true:
    #                 try:
    #                     sender = await event.get_sender()
    #                     await event.client.get_input_entity(sender)
    #                 except ValueError:
    #                     log.info(f'Error attempt get sender')
    #                     return 0
    #                 new_message_id = db_add_message(
    #                     message_id=message_instance.id,
    #                     sender_id=sender_id,
    #                     theme_name=theme,
    #                     username=username,
    #                     message=message_text,
    #                     user_id=user,
    #                     chat_unique_id=str(chat_id),
    #                     mentioned_message_id=mentioned_message_id,
    #                 )
    #                 # db_add_user_message(chat_id=BOT_ID, user_id=user_id, message=message_text)
    #                 reply_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    #                     [InlineKeyboardButton(text='Сформировать сообщение от конструктора',
    #                                           callback_data=f'incoming_message:answer:{new_message_id}')],
    #                     [InlineKeyboardButton(text='Написать собственный ответ',
    #                                           callback_data=f'incoming_message:custom_message:{new_message_id}')],
    #                     [InlineKeyboardButton(text='Добавить в спам',
    #                                           callback_data=f'incoming_message:spam:{new_message_id}')],
    #                     [InlineKeyboardButton(text='Пропустить',
    #                                           callback_data=f'incoming_message:skip:{new_message_id}')],
    #                 ])
    #                 log.info(msg=f'Send notification to user {user}')
    #                 message = await bot.send_message(
    #                     chat_id=user,
    #                     text=f'Сработали триггер темы: {theme}\nв чате: t.me/{message_instance.chat.username}/{message_instance.id}\nТекст сообщения: {message_text}',
    #                     reply_markup=reply_keyboard,
    #                 )
    #                 message_id = message.message_id
    #                 db_add_user_message(chat_id=BOT_ID, user_id=user, message_id=message_id, message=message_text)
    #                 break


async def chat_with_gpt(prompt: str, system_prompt: str, client: AsyncOpenAI, logger, model: str = "gpt-4o-mini") -> str:
    try:
        logger.debug("Making GPT request")
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        )
        logger.debug("Got GPT response", response=response)
        return response.choices[0].message.content
    except Exception as e:
        raise e
