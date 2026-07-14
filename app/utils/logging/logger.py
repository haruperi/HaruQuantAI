"""Import-safe redacted structured logging configuration."""

from __future__ import annotations

import atexit
import copy
import json
import logging
import logging.handlers
import sys
import threading
import time
import zipfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from queue import Queue
from typing import TextIO

from app.utils.errors.exceptions import ConfigurationError, HaruQuantError
from app.utils.security.redaction import (
    RedactionPolicy,
    redact_mapping_value,
    redact_text_value,
)
from app.utils.settings.models import LoggingSettings
from app.utils.time.timestamps import format_utc_timestamp

_LOGGER_ROOT = "haruquant"
_OWNED_HANDLER_ATTRIBUTE = "_haruquant_utils_handler"
_TRACE_FIELDS = (
    "request_id",
    "workflow_id",
    "correlation_id",
    "causation_id",
    "event_id",
)
_STANDARD_RECORD_FIELDS = frozenset(
    {*logging.makeLogRecord({}).__dict__, "asctime", "message"}
)
_OUTPUT_FIELDS = frozenset({"timestamp", "level", "logger", "message"})
_LEVEL_COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[1;31m",
}
_COLOR_RESET = "\033[0m"
_LISTENER_LOCK = threading.Lock()


class _LoggingRuntimeState:
    """Mutable lifecycle state protected by the listener lock."""

    def __init__(self) -> None:
        self.queue_listener: logging.handlers.QueueListener | None = None
        self.record_queue: Queue[logging.LogRecord] | None = None
        self.owned_sinks: tuple[logging.Handler, ...] = ()
        self.atexit_registered = False


_RUNTIME_STATE = _LoggingRuntimeState()


def _safe_fallback() -> None:
    try:
        sys.stderr.write("logging_configuration_failed\n")
    except OSError:
        return


class RedactingFilter(logging.Filter):
    """Redact message and structured context before formatting."""

    def __init__(self, policy: RedactionPolicy | None = None) -> None:
        """Initialize the filter with an immutable policy."""
        super().__init__()
        self._policy = policy or RedactionPolicy()

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact one record in place before formatter access.

        Args:
            record: Logging record to sanitize.

        Returns:
            Always ``True`` so the sanitized record is emitted.
        """
        safe_message = redact_text_value(record.getMessage(), self._policy)
        record.msg = safe_message.value
        record.args = ()
        if record.exc_info:
            exception_text = logging.Formatter().formatException(record.exc_info)
            safe_exception = redact_text_value(exception_text, self._policy)
            record._safe_exception = safe_exception.value  # noqa: SLF001
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_RECORD_FIELDS and not key.startswith("_")
        }
        try:
            safe_context = redact_mapping_value(extras, self._policy).value
        except HaruQuantError:
            safe_context = {"redaction_error": True}
        record._structured_context = safe_context  # noqa: SLF001
        return True


class StructuredFormatter(logging.Formatter):
    """Render sanitized logging records as JSON or human-readable text."""

    def __init__(self, render: str = "human", *, colorize: bool = False) -> None:
        """Initialize a formatter.

        Args:
            render: Exactly ``json`` or ``human``.
            colorize: Whether to color human-rendered level and message content.

        Raises:
            ConfigurationError: If the render mode is invalid.
        """
        if render not in {"json", "human"}:
            raise ConfigurationError("LOG_RENDER_INVALID")
        super().__init__()
        self._render = render
        self._colorize = colorize

    def _apply_color(self, rendered: str, level_name: str) -> str:
        if not self._colorize:
            return rendered
        color = _LEVEL_COLORS.get(level_name, "")
        if not color:
            return rendered
        return f"{color}{rendered}{_COLOR_RESET}"

    def format(self, record: logging.LogRecord) -> str:
        """Format a previously sanitized record."""
        created_at = datetime.fromtimestamp(record.created, UTC)
        timestamp = format_utc_timestamp(created_at)
        output: dict[str, object] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = getattr(record, "_structured_context", {})
        if isinstance(context, dict):
            collisions: dict[str, object] = {}
            for key, value in context.items():
                if key in _OUTPUT_FIELDS:
                    collisions[key] = value
                else:
                    output[key] = value
            if collisions:
                output["context"] = collisions
        safe_exception = getattr(record, "_safe_exception", None)
        if isinstance(safe_exception, str):
            output["exception"] = safe_exception
        if self._render == "json":
            rendered = json.dumps(
                output,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            return rendered
        context_text = " ".join(
            f"{key}={value}"
            for key, value in output.items()
            if key not in _OUTPUT_FIELDS and key != "exception"
        )
        suffix = f" | {context_text}" if context_text else ""
        human_timestamp = created_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        source_module = getattr(record, "_source_module", record.module)
        source_function = getattr(record, "_source_function", record.funcName)
        source_line = getattr(record, "_source_line", record.lineno)
        level_text = self._apply_color(f"{record.levelname:<8}", record.levelname)
        message_text = f"{record.getMessage()}{suffix}"
        if isinstance(safe_exception, str):
            message_text = f"{message_text}\n{safe_exception}"
        colored_message = self._apply_color(message_text, record.levelname)
        return (
            f"{human_timestamp} | {level_text} | "
            f"{source_module}:{source_function}:{source_line} - "
            f"{colored_message}"
        )


class _SafeErrorMixin:
    """Emit only a fixed bounded fallback when a handler fails."""

    def handleError(self, _record: logging.LogRecord) -> None:  # noqa: N802
        _safe_fallback()


class _SafeStreamHandler(_SafeErrorMixin, logging.StreamHandler[TextIO]):
    """Stream handler with secret-safe failure handling."""


class _SafeRotatingFileHandler(
    _SafeErrorMixin,
    logging.handlers.RotatingFileHandler,
):
    """Rotating file handler with ZIP compression and age retention."""

    def __init__(
        self,
        filename: Path,
        *,
        max_bytes: int,
        backup_count: int,
        retention_days: int,
        compression: str,
    ) -> None:
        """Initialize bounded size rotation and retention settings."""
        super().__init__(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        self._retention_days = retention_days
        if compression == "zip":
            self.namer = _zip_rotated_name
            self.rotator = _zip_rotator

    def doRollover(self) -> None:  # noqa: N802
        """Rotate the active file and remove expired rotated files."""
        super().doRollover()
        cutoff = time.time() - (self._retention_days * 86_400)
        base_path = Path(self.baseFilename)
        for candidate in base_path.parent.glob(f"{base_path.name}.*"):
            if candidate.is_file() and candidate.stat().st_mtime < cutoff:
                candidate.unlink()


class _PreservingQueueHandler(
    _SafeErrorMixin,
    logging.handlers.QueueHandler,
):
    """In-process queue handler that preserves traceback information."""

    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        """Copy a record without stripping exception or structured context."""
        return copy.copy(record)


class _RouteFilter(logging.Filter):
    """Select records for one specialized logging route."""

    def __init__(self, route: str) -> None:
        """Initialize an access or debug route filter."""
        super().__init__()
        self._route = route

    def filter(self, record: logging.LogRecord) -> bool:
        """Return whether a record belongs to this specialized route."""
        log_type = getattr(record, "log_type", None)
        if self._route == "access":
            return log_type == "access"
        if self._route == "debug":
            return record.levelno == logging.DEBUG
        return record.levelno >= logging.ERROR


def get_logger(name: str) -> logging.Logger:
    """Return a stable child logger without configuring handlers.

    Args:
        name: Logger name or existing ``haruquant`` child name.

    Returns:
        Stable named logger.
    """
    if name == _LOGGER_ROOT or name.startswith(f"{_LOGGER_ROOT}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{_LOGGER_ROOT}.{name}")


class BoundLogger:
    """Import-safe logger facade with immutable structured context."""

    def __init__(
        self,
        name: str = _LOGGER_ROOT,
        context: Mapping[str, object] | None = None,
    ) -> None:
        """Initialize a logger name and immutable copy of context."""
        self._name = name
        self._context = dict(context or {})

    def bind(self, **context: object) -> BoundLogger:
        """Return a new logger carrying merged structured context."""
        merged = dict(self._context)
        merged.update(context)
        return BoundLogger(self._name, merged)

    def _emit(
        self,
        level: int,
        message: str,
        *args: object,
        exc_info: bool = False,
    ) -> None:
        caller = sys._getframe(2)  # noqa: SLF001 - preserve facade caller location.
        context = dict(self._context)
        context.update(
            {
                "_source_module": caller.f_globals.get(
                    "__name__",
                    caller.f_code.co_name,
                ),
                "_source_function": caller.f_code.co_name,
                "_source_line": caller.f_lineno,
            }
        )
        get_logger(self._name).log(
            level,
            message,
            *args,
            exc_info=exc_info,
            extra=context,
            stacklevel=3,
        )

    def debug(self, message: str, *args: object) -> None:
        """Emit a DEBUG record."""
        self._emit(logging.DEBUG, message, *args)

    def info(self, message: str, *args: object) -> None:
        """Emit an INFO record."""
        self._emit(logging.INFO, message, *args)

    def warning(self, message: str, *args: object) -> None:
        """Emit a WARNING record."""
        self._emit(logging.WARNING, message, *args)

    def error(self, message: str, *args: object) -> None:
        """Emit an ERROR record."""
        self._emit(logging.ERROR, message, *args)

    def critical(self, message: str, *args: object) -> None:
        """Emit a CRITICAL record."""
        self._emit(logging.CRITICAL, message, *args)

    def exception(self, message: str, *args: object) -> None:
        """Emit an ERROR record with the current exception traceback."""
        self._emit(logging.ERROR, message, *args, exc_info=True)


logger = BoundLogger()


def _zip_rotated_name(default_name: str) -> str:
    return f"{default_name}.zip"


def _zip_rotator(source: str, destination: str) -> None:
    source_path = Path(source)
    with zipfile.ZipFile(
        destination,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.write(source_path, arcname=source_path.name)
    source_path.unlink()


def _mark_owned(handler: logging.Handler) -> logging.Handler:
    setattr(handler, _OWNED_HANDLER_ATTRIBUTE, True)
    return handler


def _build_rotating_file_handler(
    path: Path,
    settings: LoggingSettings,
) -> logging.Handler:
    resolved = Path(path)
    if not resolved.parent.is_dir():
        _safe_fallback()
        raise ConfigurationError("LOGGING_SINK_INVALID")
    try:
        return _SafeRotatingFileHandler(
            resolved,
            max_bytes=settings.max_bytes,
            backup_count=settings.backup_count,
            retention_days=settings.retention_days,
            compression=settings.compression,
        )
    except OSError:
        _safe_fallback()
        raise ConfigurationError("LOGGING_CONFIGURATION_FAILED") from None


def _build_file_handlers(settings: LoggingSettings) -> list[logging.Handler]:
    handlers: list[logging.Handler] = []
    if settings.file_path is not None:
        handlers.append(_build_rotating_file_handler(settings.file_path, settings))
    if settings.log_directory is None:
        return handlers
    directory = Path(settings.log_directory)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        _safe_fallback()
        raise ConfigurationError("LOGGING_SINK_INVALID") from None
    if not directory.is_dir():
        _safe_fallback()
        raise ConfigurationError("LOGGING_SINK_INVALID")
    app_handler = _build_rotating_file_handler(directory / "app.log", settings)
    app_handler.setLevel(settings.level)
    access_handler = _build_rotating_file_handler(directory / "access.log", settings)
    access_handler.setLevel(settings.level)
    access_handler.addFilter(_RouteFilter("access"))
    debug_handler = _build_rotating_file_handler(directory / "debug.log", settings)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.addFilter(_RouteFilter("debug"))
    error_handler = _build_rotating_file_handler(directory / "errors.log", settings)
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(_RouteFilter("error"))
    handlers.extend((app_handler, access_handler, debug_handler, error_handler))
    return handlers


def _close_current_configuration(root_logger: logging.Logger) -> None:
    if _RUNTIME_STATE.queue_listener is not None:
        _RUNTIME_STATE.queue_listener.stop()
        _RUNTIME_STATE.queue_listener = None
        _RUNTIME_STATE.record_queue = None
    for handler in tuple(root_logger.handlers):
        if getattr(handler, _OWNED_HANDLER_ATTRIBUTE, False):
            root_logger.removeHandler(handler)
            if handler not in _RUNTIME_STATE.owned_sinks:
                handler.close()
    for sink in _RUNTIME_STATE.owned_sinks:
        sink.flush()
        sink.close()
    _RUNTIME_STATE.owned_sinks = ()


def flush_logging() -> None:
    """Wait for queued records and flush Utils-owned sinks without closing them."""
    with _LISTENER_LOCK:
        if _RUNTIME_STATE.record_queue is not None:
            _RUNTIME_STATE.record_queue.join()
        for sink in _RUNTIME_STATE.owned_sinks:
            sink.flush()


def shutdown_logging() -> None:
    """Flush queued records and close every Utils-owned logging sink."""
    with _LISTENER_LOCK:
        _close_current_configuration(logging.getLogger(_LOGGER_ROOT))


def configure_logging(
    settings: LoggingSettings | None = None,
    redaction_policy: RedactionPolicy | None = None,
) -> None:
    """Explicitly configure deduplicated redacted structured handlers.

    Args:
        settings: Immutable logging settings; approved defaults when omitted.
        redaction_policy: Optional immutable redaction policy.

    Raises:
        ConfigurationError: If the settings or sink is invalid.
    """
    active_settings = settings or LoggingSettings()
    root_logger = logging.getLogger(_LOGGER_ROOT)
    console_formatter = StructuredFormatter(
        active_settings.render,
        colorize=active_settings.colorize,
    )
    file_formatter = StructuredFormatter(active_settings.render)
    redacting_filter = RedactingFilter(redaction_policy)
    try:
        console_handler = _mark_owned(_SafeStreamHandler(sys.stdout))
        console_handler.setLevel(active_settings.level)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(redacting_filter)
        file_handlers = _build_file_handlers(active_settings)
        for file_handler in file_handlers:
            _mark_owned(file_handler)
            file_handler.setFormatter(file_formatter)
            file_handler.addFilter(redacting_filter)
    except (OSError, ValueError, TypeError):
        _safe_fallback()
        raise ConfigurationError("LOGGING_CONFIGURATION_FAILED") from None

    sinks = (console_handler, *file_handlers)
    with _LISTENER_LOCK:
        _close_current_configuration(root_logger)
        _RUNTIME_STATE.owned_sinks = sinks
        if active_settings.enqueue:
            record_queue: Queue[logging.LogRecord] = Queue()
            queue_handler = _mark_owned(_PreservingQueueHandler(record_queue))
            root_logger.addHandler(queue_handler)
            listener = logging.handlers.QueueListener(
                record_queue,
                *sinks,
                respect_handler_level=True,
            )
            listener.start()
            _RUNTIME_STATE.queue_listener = listener
            _RUNTIME_STATE.record_queue = record_queue
            if not _RUNTIME_STATE.atexit_registered:
                atexit.register(shutdown_logging)
                _RUNTIME_STATE.atexit_registered = True
        else:
            for sink in sinks:
                root_logger.addHandler(sink)
        root_logger.setLevel(active_settings.level)
        root_logger.propagate = False
