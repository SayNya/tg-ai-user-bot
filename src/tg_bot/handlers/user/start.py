import asyncpg
import structlog
from aiogram import types

from src.db.repositories import UserRepository, ChatRepository
from src.tg_bot.keyboards.inline import user, callbacks
from src.user_bot.utils import UserBot


async def start(
    msg: types.Message,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
) -> None:
    if msg.from_user is None:
        return
    user_repository = UserRepository(connection_poll=db_pool, logger=db_logger)
    db_user = await user_repository.get_user_by_id(msg.from_user.id)

    if not db_user:
        await user_repository.create_user(
            user_id=msg.from_user.id,
            is_bot=msg.from_user.is_bot,
            first_name=msg.from_user.first_name,
            last_name=msg.from_user.last_name,
            username=msg.from_user.username,
            language_code=msg.from_user.language_code,
        )


async def groups_command(
    msg: types.Message,
):
    if msg.from_user is None:
        return

    m = "Выберите действие:"
    await msg.answer(m, reply_markup=user.group.GroupButtons().main())


async def choose_group_to_add(
    cb: types.CallbackQuery,
    user_bot: UserBot,
):
    if cb.from_user is None:
        return

    groups = await user_bot.get_all_groups(limit=10)

    await cb.message.answer(
        "Выберите группу для добавления",
        reply_markup=user.group.GroupButtons().groups(groups, "add"),
    )

    await cb.message.delete()
    await cb.answer()


async def add_group(
    cb: types.CallbackQuery,
    callback_data: callbacks.ChangeGroupCallbackFactory,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
):
    if cb.from_user is None:
        return

    await ChatRepository(db_pool, db_logger).add_chat(
        callback_data.id, callback_data.type, callback_data.name, cb.from_user.id
    )
    await cb.message.delete()
    await cb.message.answer("Группа успешно добавлена в обработку")


async def choose_group_to_delete(
    cb: types.CallbackQuery,
    user_bot: UserBot,
):
    if cb.from_user is None:
        return

    groups = await user_bot.get_active_groups()
    await cb.message.answer(
        "Выберите группу для удаления",
        reply_markup=user.group.GroupButtons().groups(groups, "delete"),
    )

    await cb.message.delete()
    await cb.answer()


async def delete_group(
    cb: types.CallbackQuery,
    callback_data: callbacks.ChangeGroupCallbackFactory,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
):
    if cb.from_user is None:
        return

    await ChatRepository(db_pool, db_logger).deactivate_chat(
        callback_data.id,
        cb.from_user.id,
    )
    await cb.message.delete()
    await cb.message.answer("Группа успешно удалена из обработки")
