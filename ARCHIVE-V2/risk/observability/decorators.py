"""Logging, latency, error, and metrics decorators for public risk boundaries.

Isolates performance measurement and structured logging from internal pure calculations.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from app.services.risk.observability.metrics import (
    build_latency_metric,
    emit_risk_metrics,
)
from app.utils.logger import logger as system_logger

if TYPE_CHECKING:
    from app.services.risk.observability.metrics import MetricsSink


class RiskLogger(Protocol):
    """Protocol for logging interface inside decorators."""

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log info level message."""
        ...

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log debug level message."""
        ...

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log error level message."""
        ...

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log warning level message."""
        ...


class RiskBoundaryEvent:
    """Carries logging detail across boundaries.

    Args:
        name: Event identifier.
        message: Human readable info.
        metadata: Redacted event context.
    """

    def __init__(
        self,
        name: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize risk boundary event."""
        self.name = name
        self.message = message
        self.metadata = metadata or {}


def log_risk_boundary_event(event: RiskBoundaryEvent, logger: RiskLogger) -> None:
    """Emits structured logs without raw secrets or private payloads.

    Args:
        event: The event to log.
        logger: The logger to use.
    """
    logger.info(
        f"Boundary Event [{event.name}]: {event.message} - Metadata: {event.metadata}"
    )


RiskCallableT = TypeVar("RiskCallableT", bound=Callable[..., Any])


def risk_observed(
    operation: str,
    metrics: MetricsSink,
    logger: RiskLogger | None = None,
) -> Callable[[RiskCallableT], RiskCallableT]:
    """Wrap public boundaries with logging, latency measurement, and error handling.

    Args:
        operation: The name of the operation.
        metrics: The metrics sink.
        logger: The logger instance to use.

    Returns:
        Callable: The decorated function.
    """
    active_logger = logger or system_logger

    def decorator(func: RiskCallableT) -> RiskCallableT:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            active_logger.info(f"Starting risk boundary operation: {operation}")
            t_start = time.perf_counter()
            try:
                res = func(*args, **kwargs)
                t_duration = Decimal(
                    str(round((time.perf_counter() - t_start) * 1000, 3))
                )
                active_logger.info(
                    f"Risk boundary operation '{operation}' completed in {t_duration}ms"
                )
                # Emit latency metric
                latency_event = build_latency_metric(operation, t_duration)
                emit_risk_metrics(latency_event, metrics)
                return res
            except Exception as e:
                t_duration = Decimal(
                    str(round((time.perf_counter() - t_start) * 1000, 3))
                )
                active_logger.error(
                    f"Risk boundary operation '{operation}' failed in {t_duration}ms: {e}"
                )
                latency_event = build_latency_metric(operation, t_duration)
                emit_risk_metrics(latency_event, metrics)
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def measure_risk_latency(
    operation: str,
    metrics: MetricsSink,
) -> Callable[[RiskCallableT], RiskCallableT]:
    """Record execution duration in milliseconds through the metrics sink.

    Args:
        operation: The name of the operation.
        metrics: The metrics sink.

    Returns:
        Callable: The decorated function.
    """

    def decorator(func: RiskCallableT) -> RiskCallableT:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            t_start = time.perf_counter()
            try:
                res = func(*args, **kwargs)
                t_duration = Decimal(
                    str(round((time.perf_counter() - t_start) * 1000, 3))
                )
                latency_event = build_latency_metric(operation, t_duration)
                emit_risk_metrics(latency_event, metrics)
                return res
            except Exception:
                t_duration = Decimal(
                    str(round((time.perf_counter() - t_start) * 1000, 3))
                )
                latency_event = build_latency_metric(operation, t_duration)
                emit_risk_metrics(latency_event, metrics)
                raise

        return wrapper  # type: ignore[return-value]

    return decorator
