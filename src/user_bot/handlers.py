from openai import AsyncOpenAI
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.types import Message

from src.data import config
from src.db.repositories import ChatRepository, ThemeRepository

CHECK_MESSAGE = """Ты являешься ассистентом, который классифицирует сообщения в чатах и каналах по их соответствию определённой теме. Тебе передано два входных параметра:

Тема интереса, которая описывает область или категорию информации, важную для анализа.
Сообщение, поступившее в чат или канал.
::
Задача:

Проанализировать сообщение и определить, относится ли оно к указанной теме.
Ответить только одним словом: "Да", если сообщение соответствует теме, или "Нет", если оно не соответствует.
::

Пример:
Тема интереса: "Автоматизация бизнес-процессов"
Сообщение: "Использование ботов для оптимизации задач в Telegram значительно ускоряет работу команды."
Ответ: Да

Тема интереса: "Автоматизация бизнес-процессов"
Сообщение: "Скидки на спортивные товары до 50% на этой неделе!"
Ответ: Нет

::

"""

CREATE_ANSWER = """Ты являешься сотрудником отдела продаж, который отвечает на сообщения, связанные с определённой темой. Тебе предоставлены 3 параметра:

Тема интереса — область или категория, которой нужно придерживаться при формировании ответа.
Сообщение — текст, поступивший от пользователя, который относится к теме интереса.
История сообщений (необязательно) — предыдущие сообщения в беседе, если они есть, чтобы вы могли учитывать контекст диалога.
::

Задача:

Прочитать тему интереса и сообщение.
Если предоставлена история сообщений, использовать её для понимания контекста.
Сформулировать ответ, который соответствует теме интереса, используя точные данные и логику. Ответ должен быть полезным, релевантным и лаконичным. Ответ или диалог должен заканчиваться желанием протестировать продукт (товар или услугу) - это основная цель.
::

Вот 3 параметра:


История сообщений:"""


async def my_handler(client: Client, message: Message):
    if message.from_user.id == client.me.id:
        return

    groups = await ChatRepository(
        client.db_pool, client.db_logger
    ).get_active_groups_for_user(client.me.id, [ChatType.GROUP, ChatType.SUPERGROUP])
    group_ids = [group.id for group in groups]

    if message.chat.id not in group_ids:
        return

    themes = await ThemeRepository(
        client.db_pool, client.db_logger
    ).get_themes_for_group(message.chat.id, client.me.id)

    openai_client: AsyncOpenAI = client.openai_client
    thread = await openai_client.beta.threads.create()

    for theme in themes:
        content = (
            CHECK_MESSAGE
            + f"""Вот 2 входных параметра:
Тема интереса: '{theme.description}'
Сообщение: '{message.text}'"""
        )
        await openai_client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=content
        )
        run = await openai_client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=config.CHAT_GPT_ASSISTANT_CHECK,
        )
        if run.status == "completed":
            messages = await openai_client.beta.threads.messages.list(
                thread_id=thread.id
            )
            message_check = messages.data[0].content[0].text.value
            if message_check == "Нет":
                continue

        content = (
            CREATE_ANSWER
            + f"""Вот 2 входных параметра:
Тема интереса: {theme.description}
Сообщение: {message.text}"""
        )

        await openai_client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=content
        )
        run = await openai_client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=config.CHAT_GPT_ASSISTANT_MESSAGE,
        )
        if run.status == "completed":
            messages = await openai_client.beta.threads.messages.list(
                thread_id=thread.id
            )
            await message.reply_text(
                text=messages.data[0].content[0].text.value,
                reply_to_message_id=message.id,
            )
            break
