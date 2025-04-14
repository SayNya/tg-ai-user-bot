import datetime
import io

from aiogram import types
from aiogram.fsm.context import FSMContext
from openpyxl import Workbook
from src.tg_bot.keyboards.inline import callbacks, user

from src.db.repositories.message import MessageRepository


async def report_command(msg: types.Message, state: FSMContext) -> None:
    """
    Обработчик команды /report. Предлагает выбрать временной промежуток.
    """
    if msg.from_user is None:
        return

    await msg.answer(
        "Выберите временной промежуток для отчета:",
        reply_markup=user.report.ReportButtons().main(),
    )


async def generate_report(
    cb: types.CallbackQuery,
    callback_data: callbacks.ReportCallbackFactory,
    db_pool,
    db_logger,
) -> None:
    """
    Генерация отчета на основе выбранного временного промежутка.
    """
    if cb.from_user is None:
        return

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
    message_repository = MessageRepository(db_pool, db_logger)
    messages = await message_repository.get_messages_with_details(
        user_id=cb.from_user.id, start_date=start_date
    )

    # Создаем Excel-файл
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Отчет"

    # Заголовки
    sheet.append(["ID", "Текст", "Чат ID", "Название чата", "Тема ID", "Название темы", "Отправитель ID", "Юзернейм отправителя", "Дата создания"])

    # Добавляем данные
    for message in messages:
        sheet.append(
            [
                message.id,
                message.text,
                message.chat_id,
                message.chat_name,
                message.theme_id,
                message.theme_name,
                message.sender_id,
                message.sender_username,
                message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )

    # Сохраняем файл в память
    file_stream = io.BytesIO()
    workbook.save(file_stream)
    file_stream.seek(0)

    # Создаем BufferedInputFile
    input_file = types.BufferedInputFile(
        file=file_stream.getvalue(),  # Получаем содержимое файла
        filename="report.xlsx"
    )

    # Отправляем файл пользователю
    await cb.message.answer_document(
        document=input_file,
        caption="Ваш отчет готов!",
    )
