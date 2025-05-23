import collections.abc
import typing

from aiogram import types
from aiogram.fsm.context import FSMContext

from src import exceptions

T = typing.TypeVar("T")


def chunks(
    list_to_split: typing.Sequence[T],
    chunk_size: int,
) -> collections.abc.Iterator[typing.Sequence[T]]:
    for i in range(0, len(list_to_split), chunk_size):
        yield list_to_split[i : i + chunk_size]


async def delete_message(
    message: types.Message,
    previous_bot: bool = False,
    state: FSMContext | None = None,
) -> None:
    await message.delete()

    if previous_bot:
        if not state:
            raise exceptions.StateProvideError

        data = await state.get_data()
        previous_bot_message_id = data.get("previous_bot_message_id")
        if previous_bot_message_id:
            await message.bot.delete_message(message.chat.id, previous_bot_message_id)
