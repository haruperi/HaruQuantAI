"""Central logging facade, async worker, and lifecycle."""

from __future__ import annotations

import contextlib
import contextvars
import copy
import logging
import logging.handlers
import queue
import threading
from collections.abc import Callable, Mapping, MutableMapping
from pathlib import Path
from typing import Any, override

from .security import _boundary_diagnostic, normalize_path, redact_mapping, redact_value
from .sinks import (
    DEFAULT_RING_BUFFER_CAPACITY,
    LogRingBuffer,
    _build_sinks,
    _setup_access_logger,
    clear_ws_sinks,
    register_ws_sink,
)

WORKER_FR = "FR-HOST-LOGGING-WORKER"
BOUND_LOGGER_FR = "FR-HOST-LOGGING-BOUND-LOGGER"
CORRELATION_FR = "FR-HOST-LOGGING-CORRELATION"
EXPORTS_FR = "FR-HOST-LOGGING-EXPORTS"
DEFAULT_LOG_DIR: Path = Path("data/logs")
_CORRELATION_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)
_GLOBAL_RING_BUFFER: LogRingBuffer | None = None
_GLOBAL_ENGINE: TelemetryEngine | None = None
_LOGGING_LOCK: threading.RLock = threading.RLock()
_BOOTSTRAPPED: bool = False
_OWNED_ROOT_HANDLERS: list[logging.Handler] = []
_RESERVED_RECORD_KEYS = logging.makeLogRecord({}).__dict__.keys() | {
    "message",
    "asctime",
}


def set_correlation_id(correlation_id: str) -> contextvars.Token[str | None]:
    """Set current request correlation ID in task context.

    Args:
        correlation_id: Unique correlation or trace ID string.

    Returns:
        ContextVar token for resetting.
    """
    return _CORRELATION_ID.set(correlation_id)


def reset_correlation_id(token: contextvars.Token[str | None]) -> None:
    """Reset request correlation ID using context token.

    Args:
        token: ContextVar token returned by set_correlation_id.
    """
    _CORRELATION_ID.reset(token)


def get_correlation_id() -> str | None:
    """Return current request correlation ID if set, or None.

    Returns:
        Active correlation ID string or None.
    """
    return _CORRELATION_ID.get()


def get_ring_buffer() -> LogRingBuffer:
    """Return the global log ring buffer, initializing if needed."""
    global _GLOBAL_RING_BUFFER  # noqa: PLW0603
    if _GLOBAL_RING_BUFFER is None:
        with _LOGGING_LOCK:
            if _GLOBAL_RING_BUFFER is None:
                _GLOBAL_RING_BUFFER = LogRingBuffer()
    return _GLOBAL_RING_BUFFER


class TelemetryLogger(logging.LoggerAdapter[logging.Logger]):
    """Logger adapter providing dynamic context binding, redaction, and WS sinks."""

    def __init__(
        self,
        logger: logging.Logger,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize TelemetryLogger with logger and contextual extra dict."""
        super().__init__(logger, dict(extra) if extra is not None else {})

    @property
    def context(self) -> dict[str, Any]:
        """Return a copy of the bound context attributes."""
        return dict(self.extra) if self.extra is not None else {}

    @staticmethod
    def redact_secrets(data: Any, *, fingerprint: bool = False) -> Any:
        """Recursively mask sensitive values in strings, mappings, and sequences.

        Args:
            data: Arbitrary data structure to scrub.
            fingerprint: When True, emit SHA-256 fingerprint token
                ``***REDACTED:sha256:<8-hex>***`` instead of ``***REDACTED***``.

        Returns:
            Scrubbed data structure with sensitive fields masked.
        """
        if isinstance(data, Mapping):
            return redact_mapping(data, fingerprint=fingerprint)
        return redact_value(data, fingerprint=fingerprint)

    @staticmethod
    def register_ws_sink(sink: Callable[[dict[str, Any]], None]) -> None:
        """Register a WebSocket broadcast sink receiving scrubbed log entries."""
        register_ws_sink(sink)

    def bind(self, **kwargs: Any) -> TelemetryLogger:
        """Return a new TelemetryLogger instance with merged contextual attributes."""
        merged: dict[str, Any] = {**self.context, **kwargs}
        return TelemetryLogger(self.logger, merged)

    def emit(self, level: int | str, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Route structured log event across sinks with secret redaction."""
        lvl = (
            getattr(logging, level.upper(), logging.INFO)
            if isinstance(level, str)
            else level
        )
        self.log(lvl, msg, *args, **kwargs)

    @override
    def log(self, level: int, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Emit safely, initializing async sinks only on the first emission."""
        try:
            _ensure_bootstrapped()
            kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
            super().log(level, msg, *args, **kwargs)
        except Exception:  # noqa: BLE001
            _boundary_diagnostic()

    @override
    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:
        """Process log message and keyword arguments to merge bound context."""
        extra_dict = dict(self.context)
        if "extra" in kwargs and isinstance(kwargs["extra"], Mapping):
            extra_dict.update(kwargs["extra"])

        cid = get_correlation_id()
        if cid is not None and "correlation_id" not in extra_dict:
            extra_dict["correlation_id"] = cid

        # Sanitize before exposing the record to any attached third-party handler.
        extra_dict = redact_mapping(extra_dict, fingerprint=True)
        reserved = _RESERVED_RECORD_KEYS
        kwargs["extra"] = {k: v for k, v in extra_dict.items() if k not in reserved}
        if extra_dict:
            context_str = " ".join(f"{k}={v}" for k, v in extra_dict.items())
            msg = f"{msg} [{context_str}]"
        return msg, kwargs


def get_logger(name: str) -> TelemetryLogger:
    """Return standard TelemetryLogger with dynamic context binding support."""
    return TelemetryLogger(logging.getLogger(name))


def get_access_logger() -> TelemetryLogger:
    """Return specialized TelemetryLogger routing events to data/logs/access.log."""
    return get_logger("haruquantai.access")


class _RedactingQueueHandler(logging.handlers.QueueHandler):
    """Scrub structured arguments before the queue flattens them to text."""

    @override
    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        prepared = copy.copy(record)
        prepared.args = TelemetryLogger.redact_secrets(record.args, fingerprint=True)
        queued: logging.LogRecord = super().prepare(prepared)
        queued.msg = normalize_path(str(redact_value(queued.msg, fingerprint=True)))
        return queued

    @override
    def handleError(self, record: logging.LogRecord) -> None:
        """Report queue/format failures without echoing the unsanitized record."""
        _boundary_diagnostic()


class _SafeQueueListener(logging.handlers.QueueListener):
    """Keep a failing sink from terminating delivery and stranding queue tasks."""

    @override
    def handle(self, record: logging.LogRecord) -> None:
        for handler in self.handlers:
            try:
                if not self.respect_handler_level or record.levelno >= handler.level:
                    handler.handle(record)
            except Exception:  # noqa: BLE001
                _boundary_diagnostic()


class TelemetryEngine:
    """Asynchronous queue listener engine decoupling log emission from disk I/O."""

    def __init__(
        self,
        downstream_handlers: list[logging.Handler],
        queue_size: int = 10000,
    ) -> None:
        """Initialize telemetry engine with non-blocking queue and listener thread."""
        self._queue: queue.Queue[logging.LogRecord | None] = queue.Queue(
            maxsize=queue_size
        )
        self.downstream_handlers = downstream_handlers
        self._queue_handler = _RedactingQueueHandler(self._queue)
        self._listener = _SafeQueueListener(
            self._queue,
            *self.downstream_handlers,
            respect_handler_level=True,
        )
        self._listener.start()

    @property
    def queue_handler(self) -> logging.handlers.QueueHandler:
        """Return the queue handler attached to the root logger."""
        return self._queue_handler

    def flush(self) -> None:
        """Flush all pending records synchronously through the listener."""
        self._queue.join()
        for h in self.downstream_handlers:
            with contextlib.suppress(Exception):
                h.flush()

    def stop(self) -> None:
        """Stop the background listener thread and close downstream handlers."""
        self.flush()
        with contextlib.suppress(Exception):
            self._listener.stop()
        for h in self.downstream_handlers:
            with contextlib.suppress(Exception):
                h.close()


def flush_logs() -> None:
    """Flush pending log records across all telemetry queues and sinks."""
    if _GLOBAL_ENGINE is not None:
        _GLOBAL_ENGINE.flush()
    for h in logging.getLogger().handlers:
        with contextlib.suppress(Exception):
            h.flush()


def shutdown_logging() -> None:
    """Shut down asynchronous telemetry engine and close all log file handles."""
    global _GLOBAL_ENGINE, _BOOTSTRAPPED  # noqa: PLW0603
    with _LOGGING_LOCK:
        if _GLOBAL_ENGINE is not None:
            _GLOBAL_ENGINE.stop()
            _GLOBAL_ENGINE = None
        clear_ws_sinks()
        root = logging.getLogger()
        for h in _OWNED_ROOT_HANDLERS:
            root.removeHandler(h)
            with contextlib.suppress(Exception):
                h.close()
        _OWNED_ROOT_HANDLERS.clear()
        _BOOTSTRAPPED = False


def _ensure_bootstrapped() -> None:
    """Lazily bootstrap telemetry engine if not already configured."""
    if not _BOOTSTRAPPED:
        with _LOGGING_LOCK:
            if not _BOOTSTRAPPED:
                setup_logging(DEFAULT_LOG_DIR, async_engine=True)


def setup_logging(
    log_dir: Path | str | None = None,
    *,
    level: int = logging.INFO,
    ring_buffer_size: int = DEFAULT_RING_BUFFER_CAPACITY,
    async_engine: bool = True,
    publish_log: Callable[[dict[str, Any]], None] | None = None,
) -> LogRingBuffer:
    """Configure multi-sink logging, secret redaction, and telemetry ring buffer.

    Args:
        log_dir: Target directory for log files (defaults to data/logs).
        level: Root logger severity threshold.
        ring_buffer_size: Capacity of in-memory live telemetry buffer.
        async_engine: True to run non-blocking asynchronous queue listener.
        publish_log: Optional lifecycle-owned callback receiving scrubbed entries.

    Returns:
        The configured global LogRingBuffer.
    """
    global _GLOBAL_RING_BUFFER, _GLOBAL_ENGINE, _BOOTSTRAPPED  # noqa: PLW0603
    target_dir = Path(log_dir) if log_dir is not None else DEFAULT_LOG_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    with _LOGGING_LOCK:
        if _GLOBAL_ENGINE is not None:
            _GLOBAL_ENGINE.stop()
            _GLOBAL_ENGINE = None

        _GLOBAL_RING_BUFFER = LogRingBuffer(maxlen=ring_buffer_size)
        root = logging.getLogger()
        root.setLevel(level)

        for h in _OWNED_ROOT_HANDLERS:
            root.removeHandler(h)
            with contextlib.suppress(Exception):
                h.close()
        _OWNED_ROOT_HANDLERS.clear()
        downstream_handlers = _build_sinks(
            target_dir, level, _GLOBAL_RING_BUFFER, publish_log, get_correlation_id
        )
        downstream_handlers.append(_setup_access_logger(target_dir))

        if async_engine:
            _GLOBAL_ENGINE = TelemetryEngine(downstream_handlers)
            root.addHandler(_GLOBAL_ENGINE.queue_handler)
            _OWNED_ROOT_HANDLERS.append(_GLOBAL_ENGINE.queue_handler)
        else:
            for dh in downstream_handlers:
                root.addHandler(dh)
                _OWNED_ROOT_HANDLERS.append(dh)

        _BOOTSTRAPPED = True

    logger = logging.getLogger(__name__)
    logger.info(
        "%s: logging engine initialized (target=%s, level=%s, async=%s)",
        WORKER_FR,
        target_dir,
        logging.getLevelName(level),
        async_engine,
        extra={"fr_id": WORKER_FR, "log_dir": str(target_dir)},
    )
    return _GLOBAL_RING_BUFFER
