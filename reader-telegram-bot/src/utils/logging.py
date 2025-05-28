import logging
import sys
import typing

import orjson
import structlog

from src.data import settings


def setup_logger() -> structlog.typing.FilteringBoundLogger:
    logging_level = logging.DEBUG if settings.debug else logging.INFO

    logging.basicConfig(
        level=logging_level,
        stream=sys.stdout,
    )

    log: structlog.typing.FilteringBoundLogger = structlog.get_logger(
        structlog.stdlib.BoundLogger,
    )
    shared_processors: list[structlog.typing.Processor] = [
        structlog.processors.add_log_level,
    ]
    processors: list[structlog.typing.Processor] = [*shared_processors]
    if settings.debug:
        # Pretty printing when we run in a debug mode.
        # Automatically prints pretty tracebacks when "rich" is installed
        processors.extend(
            [
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.dev.ConsoleRenderer(),
            ],
        )
    else:
        # Print JSON when we run in production.
        # Also print structured tracebacks.
        processors.extend(
            [
                structlog.processors.TimeStamper(fmt=None, utc=True),
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(serializer=orjson_dumps),
            ],
        )
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging_level),
    )
    return log


def orjson_dumps(
    v: typing.Any,
    *,
    default: typing.Callable[[typing.Any], typing.Any] | None,
) -> str:
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()
