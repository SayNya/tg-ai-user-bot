import typing

import orjson


def orjson_dumps(
    v: typing.Any,
    *,
    default: typing.Callable[[typing.Any], typing.Any] | None,
) -> str:
    return orjson.dumps(v, default=default).decode()
