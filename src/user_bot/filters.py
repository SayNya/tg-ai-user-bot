from pyrogram import filters


def dynamic_data_filter(names: list[str]) -> filters.Filter:
    async def func(flt, _, query):  # noqa: RUF029
        return flt.data == query.data

    # "data" kwarg is accessed with "flt.data" above
    return filters.create(func, names=names)
