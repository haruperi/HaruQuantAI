"""Public, import-inert facade for FEAT-HOST-LOGGING.

Implementation is in sibling modules; consumers import `app.host.logging`.
"""

from __future__ import annotations

from .cli import TelemetryLoggerCLI
from .formatting import (
    ANSI_LEVEL_COLORS as ANSI_LEVEL_COLORS,
    ANSI_RESET as ANSI_RESET,
    ERROR_BOUNDARY_FR as ERROR_BOUNDARY_FR,
    FORMATTING_FR as FORMATTING_FR,
    LogEventFormatter,
)
from .runtime import (
    BOUND_LOGGER_FR as BOUND_LOGGER_FR,
    CORRELATION_FR as CORRELATION_FR,
    DEFAULT_LOG_DIR as DEFAULT_LOG_DIR,
    EXPORTS_FR as EXPORTS_FR,
    WORKER_FR as WORKER_FR,
    TelemetryEngine,
    TelemetryLogger,
    _RedactingQueueHandler as _RedactingQueueHandler,
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
    REDACTED_STR as REDACTED_STR,
    REDACTION_FR as REDACTION_FR,
    SENSITIVE_KEY_PATTERN as SENSITIVE_KEY_PATTERN,
    SENSITIVE_VALUE_PATTERN as SENSITIVE_VALUE_PATTERN,
    fingerprint_secret,
    normalize_path,
    redact_mapping,
    redact_value,
)
from .sinks import (
    DEFAULT_RING_BUFFER_CAPACITY,
    LOG_BACKUP_COUNT as LOG_BACKUP_COUNT,
    MAX_LOG_FILE_BYTES as MAX_LOG_FILE_BYTES,
    RING_BUFFER_FR as RING_BUFFER_FR,
    SINKS_FR as SINKS_FR,
    LogRingBuffer,
    RingBufferHandler as RingBufferHandler,
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
