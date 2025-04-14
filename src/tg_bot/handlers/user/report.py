import datetime
import io

from aiogram import types
from aiogram.fsm.context import FSMContext
from openpyxl import Workbook

from src.db.repositories.message import MessageRepository


async def report_command(msg: types.Message, state: FSMContext) -> None:
    """
    Обработчик команды /report. Предлагает выбрать временной промежуток.
    """
    if msg.from_user is None:
        return

    await state.set_state("waiting_for_report_period")
    await msg.answer(
        "Выберите временной промежуток для отчета:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton("1 день")],
                [types.KeyboardButton("1 неделя")],
                [types.KeyboardButton("1 месяц")],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


async def generate_report(
    msg: types.Message,
    state: FSMContext,
    db_pool,
    db_logger,
) -> None:
    """
    Генерация отчета на основе выбранного временного промежутка.
    """
    if msg.from_user is None:
        return

    # Определяем временной промежуток
    now = datetime.datetime.utcnow()
    if msg.text == "1 день":
        start_date = now - datetime.timedelta(days=1)
    elif msg.text == "1 неделя":
        start_date = now - datetime.timedelta(weeks=1)
    elif msg.text == "1 месяц":
        start_date = now - datetime.timedelta(days=30)
    else:
        await msg.answer("Пожалуйста, выберите корректный временной промежуток.")
        return

    # Получаем данные из базы данных
    message_repository = MessageRepository(db_pool, db_logger)
    messages = await message_repository.get_messages_since(
        user_id=msg.from_user.id, start_date=start_date
    )

    # Создаем Excel-файл
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Отчет"

    # Заголовки
    sheet.append(["ID", "Текст", "Чат ID", "Пользователь ID", "Дата", "Тема ID"])

    # Добавляем данные
    for message in messages:
        sheet.append(
            [
                message.id,
                message.text,
                message.chat_id,
                message.user_id,
                message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                message.theme_id,
            ]
        )

    # Сохраняем файл в память
    file_stream = io.BytesIO()
    workbook.save(file_stream)
    file_stream.seek(0)

    # Отправляем файл пользователю
    await msg.answer_document(
        document=types.InputFile(file_stream, filename="report.xlsx"),
        caption="Ваш отчет готов!",
    )

    # Сбрасываем состояние
    await state.clear()
    