from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any, Optional
from uuid import uuid4

import structlog

from .config import get_settings

_CORRELATION_ID: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def configure_logging() -> None:
    """Configure structlog + stdlib logging with JSON output and correlation id."""

    settings = get_settings()

    logging.basicConfig(level=settings.log_level)

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer() if settings.log_json else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(settings.log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def bind_correlation_id(correlation_id: Optional[str] = None) -> str:
    value = correlation_id or str(uuid4())
    _CORRELATION_ID.set(value)
    structlog.contextvars.bind_contextvars(correlation_id=value)
    return value


def clear_correlation_id() -> None:
    _CORRELATION_ID.set(None)
    structlog.contextvars.unbind_contextvars("correlation_id")


def get_logger(*args: Any, **kwargs: Any) -> structlog.BoundLogger:
    return structlog.get_logger(*args, **kwargs)
