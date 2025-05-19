import logging
import sys

import structlog

from src.config import settings


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
                structlog.processors.JSONRenderer(),
            ],
        )
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging_level),
    )
    return log
