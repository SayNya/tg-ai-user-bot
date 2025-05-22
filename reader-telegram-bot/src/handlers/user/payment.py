from aiogram import types
from aiogram.fsm.context import FSMContext

from src.tg_bot.keyboards.inline.user.payment import PayButtons
from src.utils.modulbank_api import ModulBankApi


async def pay_command(
    msg: types.Message,
) -> None:
    user_id = msg.from_user.id
    client = user_clients.get(user_id)

    data = await client.get_payment_data()

    # Формируем текст с учетом статуса подписки
    subscription_status = "✅" if data.is_subscribed else "🚫"
    text = (
        f"Ваш баланс: {data.balance:.2f} руб.\n"
        f"Статус подписки: {subscription_status}\n\n"
        "Выберите действие:"
    )

    # Генерируем кнопки
    reply_markup = PayButtons.main(is_subscribed=data.is_subscribed)
    await msg.answer(text, reply_markup=reply_markup)


async def toggle_subscription(
    cb: types.CallbackQuery,
) -> None:
    user_id = cb.from_user.id
    client = user_clients.get(user_id)

    data = await client.get_payment_data()
    await client.update_user_subscription_status(not data.is_subscribed)

    subscription_status = "✅" if not data.is_subscribed else "🚫"
    user_id = cb.from_user.id
    text = (
        f"Ваш баланс: {data.balance:.2f} руб.\n"
        f"Статус подписки: {subscription_status}\n\n"
        "Выберите действие:"
    )

    reply_markup = PayButtons.main(is_subscribed=not data.is_subscribed)
    await cb.message.edit_text(text, reply_markup=reply_markup)


async def enter_amount(
    cb: types.CallbackQuery,
    state: FSMContext,
) -> None:
    await state.set_state(
        "waiting_for_amount",
    )  # Устанавливаем состояние ожидания суммы
    await cb.message.answer("Введите сумму, на которую вы хотите пополнить баланс:")
    await cb.answer()


async def process_amount(
    msg: types.Message,
    state: FSMContext,
    modulbank_api: ModulBankApi,
) -> None:
    try:
        amount = int(msg.text)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом.")

        user_id = msg.from_user.id
        client = user_clients.get(user_id)

        # Создаем заказ
        order_uuid = await client.create_order(amount)
        order_data = await client.get_order(order_uuid)
        if order_data is None:
            await msg.answer("Не удалось создать заказ. Попробуйте позже.")
            return

        # Подготавливаем данные для ModulBank
        content = modulbank_api.prepare_content(order_data.uuid, amount, user_id)

        # Генерируем ссылку на оплату
        payment_link = await modulbank_api.get_payment_uri(content)

        # Отправляем ссылку пользователю
        text = f"Для пополнения баланса перейдите по ссылке:\n\n{payment_link}"
        await msg.answer(text)
        await state.clear()  # Сбрасываем состояние
    except ValueError:
        await msg.answer("Пожалуйста, введите корректную сумму.")
    except Exception as e:
        await msg.answer(f"Произошла ошибка: {e!s}")
