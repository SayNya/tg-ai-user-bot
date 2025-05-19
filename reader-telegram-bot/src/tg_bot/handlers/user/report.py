import datetime
import io

from aiogram import types
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.tables import Chat, Message
from src.models import MessageWithTopicAndChat
from src.tg_bot.keyboards.inline import callbacks, user


async def report_command(msg: types.Message) -> None:
    await msg.answer(
        "Выберите временной промежуток для отчета:",
        reply_markup=user.report.ReportButtons().main(),
    )


async def generate_report(
    cb: types.CallbackQuery,
    callback_data: callbacks.ReportCallbackFactory,
    session: AsyncSession,
) -> None:
    # Определяем временной промежуток
    now = datetime.datetime.now(datetime.timezone.utc)

    period = callback_data.period
    if period == "day":
        start_date = now - datetime.timedelta(days=1)
    elif period == "week":
        start_date = now - datetime.timedelta(weeks=1)
    elif period == "month":
        start_date = now - datetime.timedelta(days=30)
    else:
        await cb.message.answer("Пожалуйста, выберите корректный временной промежуток.")
        return

    start_date = start_date.replace(tzinfo=None)

    # Получаем данные из базы данных
    stmt = (
        select(Message)
        .options(selectinload(Message.topic, Message.chat))
        .where(
            Chat.user_id == cb.from_user.id,
            Message.created_at >= start_date,
        )
        .order_by(Message.created_at)
    )
    result = await session.scalars(stmt).all()

    messages = [MessageWithTopicAndChat.model_validate(row) for row in result]

    # Создаем Excel-файл
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Отчет"

    # Заголовки
    sheet.append(
        [
            "ID сообщения",
            "Telegram ID сообщения",
            "Тип отправителя",
            "Имя пользователя отправителя",
            "Содержание сообщения",
            "Оценка уверенности",
            "ID чата",
            "Название чата",
            "ID темы",
            "Название темы",
            "ID родительского сообщения",
            "Дата и время создания",
        ],
    )

    # Добавляем данные
    for message in messages:
        sheet.append(
            [
                message.id,
                message.telegram_message_id,
                message.sender_type,
                message.sender_username,
                message.content,
                message.confidence_score,
                message.chat.telegram_chat_id,
                message.chat.title,
                message.topic.id,
                message.topic.name,
                message.parent_message_id,
                message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ],
        )

    # Сохраняем файл в память
    file_stream = io.BytesIO()
    workbook.save(file_stream)
    file_stream.seek(0)

    # Создаем BufferedInputFile
    input_file = types.BufferedInputFile(
        file=file_stream.getvalue(),
        filename="report.xlsx",  # Получаем содержимое файла
    )

    # Отправляем файл пользователю
    await cb.message.answer_document(
        document=input_file,
        caption="Ваш отчет готов!",
    )
