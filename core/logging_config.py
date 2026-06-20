import logging
import sys
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import structlog

from app.domain.exceptions import DomainError
from core.config import get_settings

F = TypeVar("F", bound=Callable[..., Any])


def _safe_repr(value: Any, max_len: int = 200) -> Any:
    if isinstance(value, str) and len(value) > max_len:
        return value[:max_len] + "..."
    if isinstance(value, dict):
        return {k: _safe_repr(v, max_len) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_safe_repr(v, max_len) for v in value]
    if hasattr(value, "hex"):
        return str(value)
    return value


def setup_logging() -> None:
    settings = get_settings()
    level = logging.DEBUG if settings.debug else logging.INFO

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


def log_use_case(use_case_name: str) -> Callable[[F], F]:
    logger = get_logger("use_case")

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info(
                "use_case_invocation",
                use_case=use_case_name,
                args=_safe_repr(args[1:]),  # skip self
                kwargs=_safe_repr(kwargs),
            )
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.info(
                    "use_case_completed",
                    use_case=use_case_name,
                    duration_ms=duration_ms,
                )
                return result
            except DomainError as exc:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.warning(
                    "domain_error",
                    use_case=use_case_name,
                    error_type=type(exc).__name__,
                    message=exc.message,
                    duration_ms=duration_ms,
                )
                raise
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.error(
                    "use_case_error",
                    use_case=use_case_name,
                    error_type=type(exc).__name__,
                    message=str(exc),
                    duration_ms=duration_ms,
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator
