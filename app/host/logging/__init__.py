"""Public, import-inert facade for FEAT-HOST-LOGGING.

The implementation lives in sibling files. Consumers import only this package.
Use `python -m app.host.logging --verify` for the host logging diagnostic.
"""
from __future__ import annotations
from .cli import TelemetryLoggerCLI
from .formatting import ERROR_BOUNDARY_FR, FORMATTING_FR, LogEventFormatter, ANSI_RESET
from .runtime import (
    WORKER_FR, BOUND_LOGGER_FR, CORRELATION_FR, EXPORTS_FR,
    TelemetryEngine, TelemetryLogger, flush_logs, get_access_logger,
    get_correlation_id, get_logger, get_ring_buffer, reset_correlation_id,
    set_correlation_id, setup_logging, shutdown_logging, _RedactingQueueHandler,
)
from .security import (
    REDACTED_STR, REDACTION_FR, fingerprint_secret, normalize_path, redact_mapping, redact_value,
)
from .sinks import (
    SINKS_FR, RING_BUFFER_FR, DEFAULT_RING_BUFFER_CAPACITY, LOG_BACKUP_COUNT,
    MAX_LOG_FILE_BYTES, LogRingBuffer, WindowsSafeRotatingFileHandler,
)

__all__ = [
    "DEFAULT_RING_BUFFER_CAPACITY", "LogEventFormatter", "LogRingBuffer",
    "TelemetryEngine", "TelemetryLogger", "TelemetryLoggerCLI",
    "WindowsSafeRotatingFileHandler", "fingerprint_secret", "flush_logs",
    "get_access_logger", "get_correlation_id", "get_logger", "get_ring_buffer",
    "normalize_path", "redact_mapping", "redact_value", "reset_correlation_id",
    "set_correlation_id", "setup_logging", "shutdown_logging",
]
