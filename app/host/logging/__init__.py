"""Public host logging API.

One logging feature, internally decomposed into focused implementation modules.
Import from `app.host.logging` for the application-facing logging API.
"""

from __future__ import annotations

from .cli import TelemetryLoggerCLI
from .formatting import LogEventFormatter
from .runtime import (
    TelemetryEngine,
    TelemetryLogger,
    flush_logs,
    get_access_logger,
    get_correlation_id,
    get_logger,
    get_ring_buffer,
    reset_correlation_id,
    set_correlation_id,
    setup_logging,
    shutdown_logging,
)
from .security import (
    fingerprint_secret,
    normalize_path,
    redact_mapping,
    redact_value,
)
from .sinks import (
    DEFAULT_RING_BUFFER_CAPACITY,
    LogRingBuffer,
    WindowsSafeRotatingFileHandler,
)

__all__ = [
    "DEFAULT_RING_BUFFER_CAPACITY",
    "LogEventFormatter",
    "LogRingBuffer",
    "TelemetryEngine",
    "TelemetryLogger",
    "TelemetryLoggerCLI",
    "WindowsSafeRotatingFileHandler",
    "fingerprint_secret",
    "flush_logs",
    "get_access_logger",
    "get_correlation_id",
    "get_logger",
    "get_ring_buffer",
    "normalize_path",
    "redact_mapping",
    "redact_value",
    "reset_correlation_id",
    "set_correlation_id",
    "setup_logging",
    "shutdown_logging",
]
