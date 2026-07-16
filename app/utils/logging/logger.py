"""Configure import-safe, redacted, bounded structured logging.

Imports are inert. Explicit configuration or the first runtime ``BoundLogger``
emission installs owned handlers, and explicit shutdown closes only those
handlers and their optional queue listener.
"""

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
from types import FrameType
from typing import TextIO

from app.utils.errors.exceptions import ConfigurationError, HaruQuantError
from app.utils.security.redaction import RedactionPolicy, _redact_mapping, _redact_text
from app.utils.settings.models import LoggingSettings
from app.utils.time.timestamps import format_utc_timestamp

_LOGGER_ROOT = "haruquant"
_OWNED_HANDLER_ATTRIBUTE = "_haruquant_utils_handler"
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
_LISTENER_LOCK = threading.RLock()


class _LoggingRuntimeState:
    """Hold process-local logging lifecycle state behind the listener lock.

    Attributes:
        queue_listener: Active owned queue listener, when queued delivery is on.
        record_queue: Queue consumed by ``queue_listener``.
        owned_sinks: Console and file handlers owned by Utils.
        atexit_registered: Whether process-exit cleanup was registered.
    """

    def __init__(self) -> None:
        """Initialize an inactive logging runtime state."""
        self.queue_listener: logging.handlers.QueueListener | None = None
        self.record_queue: Queue[logging.LogRecord] | None = None
        self.owned_sinks: tuple[logging.Handler, ...] = ()
        self.atexit_registered = False


_RUNTIME_STATE = _LoggingRuntimeState()


def _safe_fallback() -> None:
    """Emit the fixed bounded configuration-failure marker to stderr.

    The fallback intentionally excludes exception text, paths, settings, and
    source record values. An unavailable stderr stream is silently ignored so
    error reporting cannot recursively fail.
    """
    try:
        sys.stderr.write("logging_configuration_failed\n")
    except OSError:
        return


class RedactingFilter(logging.Filter):
    """Redact a log record before any configured formatter observes it."""

    def __init__(self, policy: RedactionPolicy | None = None) -> None:
        """Initialize the filter with an immutable policy.

        Args:
            policy: Explicit redaction policy, or the approved default when
                omitted.
        """
        super().__init__()
        self._policy = policy or RedactionPolicy()

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitize a record before formatter access.

        The method replaces the message, removes interpolation arguments,
        stores a safe traceback copy, and writes redacted structured context to
        private record attributes.

        Args:
            record: Mutable standard-library log record to sanitize in place.

        Returns:
            Always ``True`` so the sanitized record continues to the sink.
        """
        record.msg = _redact_text(record.getMessage(), self._policy)
        record.args = ()
        if record.exc_info:
            exception_text = logging.Formatter().formatException(record.exc_info)
            record._safe_exception = _redact_text(  # noqa: SLF001
                exception_text,
                self._policy,
            )
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_RECORD_FIELDS and not key.startswith("_")
        }
        try:
            safe_context = _redact_mapping(extras, self._policy)
        except HaruQuantError:
            safe_context = {"redaction_error": True}
        record._structured_context = safe_context  # noqa: SLF001
        return True


class StructuredFormatter(logging.Formatter):
    """Render sanitized records as JSON or source-aware human text."""

    def __init__(self, render: str = "human", *, colorize: bool = False) -> None:
        """Initialize a formatter for an approved render mode.

        Args:
            render: Exactly ``json`` or ``human``.
            colorize: Whether human level and message text receive ANSI color.

        Raises:
            ConfigurationError: ``render`` is not an approved mode.
        """
        if render not in {"json", "human"}:
            raise ConfigurationError("LOG_RENDER_INVALID")
        super().__init__()
        self._render = render
        self._colorize = colorize

    def _apply_color(self, rendered: str, level_name: str) -> str:
        """Apply the configured ANSI color for a standard level.

        Args:
            rendered: Already formatted text fragment.
            level_name: Standard logging level name.

        Returns:
            The original fragment or a color-wrapped copy.
        """
        if not self._colorize:
            return rendered
        color = _LEVEL_COLORS.get(level_name, "")
        return rendered if not color else f"{color}{rendered}{_COLOR_RESET}"

    def format(self, record: logging.LogRecord) -> str:
        """Format a previously sanitized record.

        Args:
            record: Log record already processed by ``RedactingFilter``.

        Returns:
            Compact sorted JSON or the approved source-aware human record.
        """
        created_at = datetime.fromtimestamp(record.created, UTC)
        output: dict[str, object] = {
            "timestamp": format_utc_timestamp(created_at),
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
            return json.dumps(
                output,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        context_text = " ".join(
            f"{key}={value}"
            for key, value in output.items()
            if key not in _OUTPUT_FIELDS and key != "exception"
        )
        suffix = f" | {context_text}" if context_text else ""
        message = f"{record.getMessage()}{suffix}"
        if isinstance(safe_exception, str):
            message = f"{message}\n{safe_exception}"
        level_text = self._apply_color(f"{record.levelname:<8}", record.levelname)
        message_text = self._apply_color(message, record.levelname)
        timestamp = created_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        source_module = getattr(record, "_source_module", record.module)
        source_function = getattr(record, "_source_function", record.funcName)
        source_line = getattr(record, "_source_line", record.lineno)
        return (
            f"{timestamp} | {level_text} | "
            f"{source_module}:{source_function}:{source_line} - {message_text}"
        )


class _SafeErrorMixin:
    """Replace standard handler diagnostics with the fixed safe fallback."""

    def handleError(self, _record: logging.LogRecord) -> None:  # noqa: N802
        """Report a handler failure without exposing source values.

        Args:
            _record: Failed record, intentionally ignored to prevent leakage.
        """
        _safe_fallback()


class _SafeStreamHandler(_SafeErrorMixin, logging.StreamHandler[TextIO]):
    """Write stream records with secret-safe handler failure reporting."""


class _SafeRotatingFileHandler(
    _SafeErrorMixin,
    logging.handlers.RotatingFileHandler,
):
    """Rotate bounded files with optional ZIP compression and age cleanup."""

    def __init__(
        self,
        filename: Path,
        *,
        max_bytes: int,
        backup_count: int,
        retention_days: int,
        compression: str,
    ) -> None:
        """Initialize bounded rotation and retention settings.

        Args:
            filename: Existing-parent path of the active log file.
            max_bytes: File-size threshold that triggers rollover.
            backup_count: Maximum numbered rotations retained by the handler.
            retention_days: Maximum rotation age removed during rollover.
            compression: ``zip`` or ``none``.

        Raises:
            OSError: The file cannot be opened by the standard handler.
        """
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
        """Rotate the active file and remove expired rotations.

        Raises:
            OSError: Rotation, file inspection, or cleanup fails.
        """
        super().doRollover()
        cutoff = time.time() - self._retention_days * 86_400
        base_path = Path(self.baseFilename)
        for candidate in base_path.parent.glob(f"{base_path.name}.*"):
            if candidate.is_file() and candidate.stat().st_mtime < cutoff:
                candidate.unlink()


class _PreservingQueueHandler(_SafeErrorMixin, logging.handlers.QueueHandler):
    """Enqueue a shallow record copy without stripping traceback evidence."""

    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        """Copy a record without stripping exception information.

        Args:
            record: Source log record submitted by a producer thread.

        Returns:
            A shallow copy safe for queue handoff.
        """
        return copy.copy(record)


class _RouteFilter(logging.Filter):
    """Select records for one access, debug, or error file route."""

    def __init__(self, route: str) -> None:
        """Initialize a specialized route filter.

        Args:
            route: Internal route name: ``access``, ``debug``, or ``error``.
        """
        super().__init__()
        self._route = route

    def filter(self, record: logging.LogRecord) -> bool:
        """Return whether a record belongs to this route.

        Args:
            record: Candidate log record.

        Returns:
            ``True`` for access-context records on the access route, exact
            DEBUG records on the debug route, or ERROR-and-higher records on
            the error route.
        """
        if self._route == "access":
            return getattr(record, "log_type", None) == "access"
        if self._route == "debug":
            return record.levelno == logging.DEBUG
        return record.levelno >= logging.ERROR


def get_logger(name: str) -> logging.Logger:
    """Return a stable child logger without configuring handlers.

    Args:
        name: Child name or an already qualified ``haruquant`` logger name.

    Returns:
        The standard-library logger for the normalized name.
    """
    if name == _LOGGER_ROOT or name.startswith(f"{_LOGGER_ROOT}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{_LOGGER_ROOT}.{name}")


class BoundLogger:
    """Emit through an import-safe logger with immutable bound context.

    Bound instances copy caller context. The first runtime emission lazily
    installs the approved default profile unless an explicit profile is active.

    Attributes:
        _name: Qualified or child logger name resolved at emission time.
        _context: Private copy of structured caller context.
    """

    def __init__(
        self,
        name: str = _LOGGER_ROOT,
        context: Mapping[str, object] | None = None,
    ) -> None:
        """Initialize a logger name and private context copy.

        Args:
            name: Logger name passed through ``get_logger`` at emission time.
            context: Optional structured context copied into this instance.
        """
        self._name = name
        self._context = dict(context or {})

    def bind(self, **context: object) -> BoundLogger:
        """Return a new logger carrying merged structured context.

        Args:
            **context: Values to add or replace in the new bound context.

        Returns:
            A distinct ``BoundLogger``; the current instance is unchanged.
        """
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
        """Emit one record with lazy setup and caller-source evidence.

        Args:
            level: Standard-library numeric log level.
            message: Message or interpolation template.
            *args: Positional values consumed by standard logging formatting.
            exc_info: Whether to capture the active exception traceback.

        Raises:
            ConfigurationError: Lazy default logging cannot create its sinks.
        """
        _ensure_default_configuration()
        caller = sys._getframe(2)  # noqa: SLF001
        context = dict(self._context)
        context.update(
            {
                "_source_module": caller.f_globals.get(
                    "__name__", caller.f_code.co_name
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
        """Emit a DEBUG record.

        Args:
            message: Message or interpolation template.
            *args: Positional interpolation values.

        Raises:
            ConfigurationError: Lazy default configuration fails.
        """
        self._emit(logging.DEBUG, message, *args)

    def info(self, message: str, *args: object) -> None:
        """Emit an INFO record.

        Args:
            message: Message or interpolation template.
            *args: Positional interpolation values.

        Raises:
            ConfigurationError: Lazy default configuration fails.
        """
        self._emit(logging.INFO, message, *args)

    def warning(self, message: str, *args: object) -> None:
        """Emit a WARNING record.

        Args:
            message: Message or interpolation template.
            *args: Positional interpolation values.

        Raises:
            ConfigurationError: Lazy default configuration fails.
        """
        self._emit(logging.WARNING, message, *args)

    def error(self, message: str, *args: object) -> None:
        """Emit an ERROR record.

        Args:
            message: Message or interpolation template.
            *args: Positional interpolation values.

        Raises:
            ConfigurationError: Lazy default configuration fails.
        """
        self._emit(logging.ERROR, message, *args)

    def critical(self, message: str, *args: object) -> None:
        """Emit a CRITICAL record.

        Args:
            message: Message or interpolation template.
            *args: Positional interpolation values.

        Raises:
            ConfigurationError: Lazy default configuration fails.
        """
        self._emit(logging.CRITICAL, message, *args)

    def exception(self, message: str, *args: object) -> None:
        """Emit an ERROR record with the current traceback.

        Args:
            message: Message or interpolation template.
            *args: Positional interpolation values.

        Raises:
            ConfigurationError: Lazy default configuration fails.
        """
        self._emit(logging.ERROR, message, *args, exc_info=True)


logger = BoundLogger()


def _ensure_default_configuration() -> None:
    """Install the approved default once before a runtime emission.

    Import-stack emissions remain inert. Runtime calls serialize setup through
    the listener lock and preserve any explicit active configuration.

    Raises:
        ConfigurationError: Default sinks cannot be configured.
    """
    frame: FrameType | None = sys._getframe(1)  # noqa: SLF001
    while frame is not None:
        module_name = str(frame.f_globals.get("__name__", ""))
        if module_name.startswith(("_frozen_importlib", "importlib._bootstrap")):
            return
        frame = frame.f_back
    with _LISTENER_LOCK:
        if not _RUNTIME_STATE.owned_sinks:
            configure_logging()


def _zip_rotated_name(default_name: str) -> str:
    """Return the ZIP filename used for a numbered rotation.

    Args:
        default_name: Filename selected by ``RotatingFileHandler``.

    Returns:
        The filename with a ``.zip`` suffix.
    """
    return f"{default_name}.zip"


def _zip_rotator(source: str, destination: str) -> None:
    """Compress one rotation and remove its uncompressed source.

    Args:
        source: Existing uncompressed rotation path.
        destination: ZIP archive path selected by the handler.

    Raises:
        OSError: Source/archive filesystem operations fail.
        zipfile.BadZipFile: Archive creation fails structurally.
    """
    source_path = Path(source)
    with zipfile.ZipFile(
        destination,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.write(source_path, arcname=source_path.name)
    source_path.unlink()


def _mark_owned(handler: logging.Handler) -> logging.Handler:
    """Mark a handler as owned by the Utils logging lifecycle.

    Args:
        handler: Handler created for the active configuration.

    Returns:
        The same handler after setting the private ownership marker.
    """
    setattr(handler, _OWNED_HANDLER_ATTRIBUTE, True)
    return handler


def _build_rotating_file_handler(
    path: Path,
    settings: LoggingSettings,
) -> logging.Handler:
    """Create one bounded rotating file handler.

    Args:
        path: Active file path whose parent must already exist.
        settings: Validated logging bounds and compression mode.

    Returns:
        An unopened-to-callers owned-capable rotating handler.

    Raises:
        ConfigurationError: The parent is unavailable or the sink cannot open.
    """
    if not path.parent.is_dir():
        _safe_fallback()
        raise ConfigurationError("LOGGING_SINK_INVALID")
    try:
        return _SafeRotatingFileHandler(
            path,
            max_bytes=settings.max_bytes,
            backup_count=settings.backup_count,
            retention_days=settings.retention_days,
            compression=settings.compression,
        )
    except OSError:
        _safe_fallback()
        raise ConfigurationError("LOGGING_CONFIGURATION_FAILED") from None


def _build_file_handlers(settings: LoggingSettings) -> list[logging.Handler]:
    """Build the configured application and specialized file handlers.

    Args:
        settings: Validated logging configuration.

    Returns:
        File handlers in deterministic application/access/debug/error order,
        preceded by the optional standalone application handler.

    Raises:
        ConfigurationError: A directory or file sink cannot be created.
    """
    handlers: list[logging.Handler] = []
    if settings.file_path is not None:
        handlers.append(_build_rotating_file_handler(settings.file_path, settings))
    if settings.log_directory is None:
        return handlers
    directory = settings.log_directory
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
    """Stop and detach the currently owned logging configuration.

    This stops the queue listener, flushes and closes owned sinks, removes
    owned root handlers, and resets process-local runtime state.

    Args:
        root_logger: HaruQuant root logger holding Utils-owned handlers.
    """
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
    """Synchronize queued delivery without closing sinks.

    The function waits for the active record queue to drain, then flushes every
    Utils-owned sink. Calling it before configuration is a safe no-op.
    """
    with _LISTENER_LOCK:
        if _RUNTIME_STATE.record_queue is not None:
            _RUNTIME_STATE.record_queue.join()
        for sink in _RUNTIME_STATE.owned_sinks:
            sink.flush()


def shutdown_logging() -> None:
    """Flush queued records and close all Utils-owned sinks.

    The operation is idempotent and does not remove handlers owned by other
    libraries or application domains.
    """
    with _LISTENER_LOCK:
        _close_current_configuration(logging.getLogger(_LOGGER_ROOT))


def configure_logging(
    settings: LoggingSettings | None = None,
    redaction_policy: RedactionPolicy | None = None,
) -> None:
    """Install a complete redacted structured-logging configuration.

    The call replaces only Utils-owned handlers. It may create the configured
    directory and files, start one queue-listener thread, and register
    process-exit cleanup once when queued delivery is selected.

    Args:
        settings: Explicit validated logging profile, or approved defaults.
        redaction_policy: Explicit immutable redaction policy, or defaults.

    Raises:
        ConfigurationError: A render mode, directory, file, or handler cannot
            be configured. Before raising, only the fixed safe fallback is
            emitted to stderr.
    """
    active_settings = settings or LoggingSettings()
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

    root_logger = logging.getLogger(_LOGGER_ROOT)
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
