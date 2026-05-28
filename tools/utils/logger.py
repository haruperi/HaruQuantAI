"""Production logging utilities for HaruQuantAI.

Provides production logging utilities for HaruQuantAI infrastructure, tools,
agents, workflows, and multiprocessing workers.

This module contains two official AI-callable utility tools:
    - init_worker_logger: routes worker-process log records through a queue.
    - configure_multiprocess_listener: starts a main-process queue listener.

The remaining classes and functions are logging infrastructure helpers. They are
not intended to be called directly by agents unless explicitly exported by the
`tools.utils` domain registry.

Classes:
    StructlogAdapter: Project logger adapter with sink support and context binding.
    CompatRecord: Structured log record dispatched to custom sinks.
    _SizeAndTimeRotatingFileSink: File sink that rotates by size and UTC day.

Internal Helpers:
    _configure_structlog
    _make_clean_console_renderer
    _safe_redact_mapping
    _safe_redact_text
    _build_tool_response
    _build_tool_metadata
    _init_worker_logger
    _configure_multiprocess_listener
"""

from __future__ import annotations

import importlib
import inspect
import logging
import os
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, Optional

from tools.utils.security import _redact_mapping, _redact_text

try:
    _STRUCTLOG_MODULE: Any = importlib.import_module("structlog")
    _HAS_STRUCTLOG = True
except ModuleNotFoundError:
    _STRUCTLOG_MODULE = None
    _HAS_STRUCTLOG = False

_FALLBACK_LOGGER = logging.getLogger(__name__)

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = False
WRITES_FILE = True
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False

DEFAULT_LOG_DIR = Path(os.environ.get("HQT_LOG_DIR", "data/logs"))
DEFAULT_MAX_BYTES = int(os.environ.get("HQT_LOG_MAX_BYTES", str(50 * 1024 * 1024)))
DEFAULT_BACKUP_COUNT = int(os.environ.get("HQT_LOG_BACKUP_COUNT", "30"))

_LEVELS: Dict[str, int] = {
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "SUCCESS": 25,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}
_LEVEL_ALIASES: Dict[str, str] = {"WARN": "WARNING", "FATAL": "CRITICAL"}
_CONTEXT_ID_KEYS = ("correlation_id", "run_id", "trace_id")

TRACE = "TRACE"
DEBUG = "DEBUG"
INFO = "INFO"
SUCCESS = "SUCCESS"
WARNING = "WARNING"
ERROR = "ERROR"
CRITICAL = "CRITICAL"
DEFAULT_LEVELS = dict(_LEVELS)

_STRUCTLOG_CONFIGURED = False
_CONFIG_LOCK = threading.Lock()
_DEFAULT_FILE_SINKS_CONFIGURED = False
_WORKER_LOG_QUEUE: Optional[Any] = None
_QUEUE_LISTENER_RUNNING = False
_QUEUE_LISTENER_LOCK = threading.Lock()


@dataclass(frozen=True)
class _CompatLevel:
    """Represents a normalized log level name and numeric severity."""

    name: str
    no: int


@dataclass
class CompatRecord:
    """Structured log record sent to custom sinks and multiprocessing queues."""

    time: datetime
    level: _CompatLevel
    message: str
    name: str
    file: str
    function: str
    line: int
    correlation_id: str
    run_id: str
    trace_id: str
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class _SinkEntry:
    """Internal sink registration metadata used by StructlogAdapter."""

    sink: Any
    level_no: int
    raw: bool
    format_string: Optional[str]
    filter_func: Optional[Callable[[CompatRecord], bool]]
    colorize: bool
    close_on_remove: bool = False


class _Core:
    """Mutable shared logger state protected by a lock."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.next_id = 1
        self.sinks: Dict[int, _SinkEntry] = {}
        self.min_level_no = _LEVELS["TRACE"]
        self.component_levels: Dict[str, int] = {}


def _safe_redact_mapping(value: Dict[str, Any]) -> Dict[str, Any]:
    """Redact a mapping using the project security utility when available."""
    try:
        return _redact_mapping(value)
    except Exception as error:  # pylint: disable=broad-exception-caught
        _FALLBACK_LOGGER.warning("Mapping redaction failed: %s", error)
        return dict(value)


def _safe_redact_text(value: str) -> str:
    """Redact a text value using the project security utility when available."""
    try:
        return _redact_text(value)
    except Exception as error:  # pylint: disable=broad-exception-caught
        _FALLBACK_LOGGER.warning("Text redaction failed: %s", error)
        return str(value)


class _SizeAndTimeRotatingFileSink:
    """Writable file sink that rotates by file size and by UTC day."""

    def __init__(self, path: Path, *, max_bytes: int, backup_count: int) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be greater than zero.")
        if backup_count <= 0:
            raise ValueError("backup_count must be greater than zero.")

        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._max_bytes = int(max_bytes)
        self._backup_count = int(backup_count)
        self._lock = threading.Lock()
        self._stream = self._path.open("a", encoding="utf-8")
        self._next_day_rollover = self._next_utc_midnight_ts()

    def write(self, text: str) -> None:
        """Write text to the sink, rotating first when needed."""
        payload = str(text)
        payload_size = len(payload.encode("utf-8"))
        with self._lock:
            if self._should_rotate(payload_size):
                self._rotate()
            self._stream.write(payload)
            self._stream.flush()

    def flush(self) -> None:
        """Flush the underlying file stream."""
        with self._lock:
            self._stream.flush()

    def close(self) -> None:
        """Close the underlying file stream."""
        with self._lock:
            self._stream.close()

    def _should_rotate(self, payload_size: int) -> bool:
        by_time = time.time() >= self._next_day_rollover
        current_size = self._path.stat().st_size if self._path.exists() else 0
        by_size = (current_size + payload_size) > self._max_bytes
        return by_time or by_size

    def _rotate(self) -> None:
        self._stream.close()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        rotated = self._path.with_name(f"{self._path.name}.{stamp}")
        suffix = 1
        while rotated.exists():
            rotated = self._path.with_name(f"{self._path.name}.{stamp}.{suffix}")
            suffix += 1
        if self._path.exists():
            self._path.rename(rotated)
        self._stream = self._path.open("a", encoding="utf-8")
        self._next_day_rollover = self._next_utc_midnight_ts()
        self._prune_old_backups()

    def _prune_old_backups(self) -> None:
        pattern = f"{self._path.name}.*"
        backups = [
            p
            for p in self._path.parent.iterdir()
            if p.is_file() and fnmatch(p.name, pattern)
        ]
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for old_file in backups[self._backup_count :]:
            try:
                old_file.unlink()
            except OSError as error:
                _FALLBACK_LOGGER.warning(
                    "Could not remove old log backup %s: %s", old_file, error
                )

    @staticmethod
    def _next_utc_midnight_ts() -> float:
        now = datetime.now(timezone.utc)
        next_midnight = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        return next_midnight.timestamp()


def _make_clean_console_renderer(
    colors: bool = True,
) -> Callable[[Any, str, Dict[str, Any]], str]:
    """Create a compact structlog console renderer."""
    empty_ok_keys = frozenset({"correlation_id", "run_id", "trace_id", "causation_id"})
    color_map: Dict[str, str] = {
        "trace": "\033[36m",
        "debug": "\033[34m",
        "info": "\033[32m",
        "success": "\033[92m",
        "warning": "\033[33m",
        "error": "\033[31m",
        "critical": "\033[91m",
    }
    reset = "\033[0m"

    def _renderer(_logger: Any, _method: str, event_dict: Dict[str, Any]) -> str:
        ts = event_dict.get("timestamp", "")
        level = str(
            event_dict.get("log_level") or event_dict.get("level", "info")
        ).lower()
        message = str(event_dict.get("event", ""))
        file_name = event_dict.get("file", "")
        function = event_dict.get("function", "")
        line = event_dict.get("line", "")
        location = f"{file_name}:{function}:{line}" if file_name else ""
        color = color_map.get(level, "") if colors else ""
        level_display = f"{color}{level.upper()}{reset}" if color else level.upper()

        extras: Dict[str, Any] = {}
        for key, item in (event_dict.get("extra") or {}).items():
            if key in empty_ok_keys and not item:
                continue
            extras[key] = item
        for key in ("exception", "stack_info"):
            if event_dict.get(key):
                extras[key] = event_dict[key]

        parts = [ts, level_display, location, message]
        if extras:
            parts.append("  ".join(f"{key}={item}" for key, item in extras.items()))
        return " | ".join(part for part in parts if part)

    return _renderer


def _configure_structlog() -> None:
    """Configure structlog once when the optional dependency is installed."""
    global _STRUCTLOG_CONFIGURED  # pylint: disable=global-statement
    if not _HAS_STRUCTLOG or _STRUCTLOG_CONFIGURED:
        return
    with _CONFIG_LOCK:
        render_mode = os.environ.get("HQT_LOG_RENDER", "console").strip().lower()
        use_colors = getattr(sys.stderr, "isatty", lambda: False)()
        final_renderer = (
            _STRUCTLOG_MODULE.processors.JSONRenderer()
            if render_mode == "json"
            else _make_clean_console_renderer(colors=use_colors)
        )
        _STRUCTLOG_MODULE.configure(
            processors=[
                _STRUCTLOG_MODULE.stdlib.add_log_level,
                _STRUCTLOG_MODULE.processors.TimeStamper(
                    fmt="%Y-%m-%d %H:%M:%S",
                    key="timestamp",
                ),
                _STRUCTLOG_MODULE.processors.StackInfoRenderer(),
                _STRUCTLOG_MODULE.processors.format_exc_info,
                final_renderer,
            ],
            context_class=dict,
            logger_factory=_STRUCTLOG_MODULE.PrintLoggerFactory(file=sys.stderr),
            cache_logger_on_first_use=True,
        )
        _STRUCTLOG_CONFIGURED = True


class StructlogAdapter:
    """Project logger adapter used by HaruQuant production modules."""

    def __init__(
        self,
        *,
        name: str = "haruquant",
        core: Optional[_Core] = None,
        bound_extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        _configure_structlog()
        self._name = name
        self._core = core or _Core()
        self._bound_extra: Dict[str, Any] = dict(bound_extra or {})
        self._logger = (
            _STRUCTLOG_MODULE.get_logger(name).bind(**self._bound_extra)
            if _HAS_STRUCTLOG
            else logging.getLogger(name)
        )

    def add(self, sink: Any, **options: Any) -> int:
        """Register a sink and return its handler ID."""
        level_name = self._normalize_level_name(options.get("level", "INFO"))
        level_no = _LEVELS[level_name]
        raw = bool(options.get("raw", False))
        fmt = options.get("format")
        filter_func = options.get("filter")
        colorize_opt = options.get("colorize")
        resolved_sink = sink
        close_on_remove = bool(options.get("close_on_remove", False))

        if isinstance(sink, (str, Path)):
            path = Path(sink)
            path.parent.mkdir(parents=True, exist_ok=True)
            resolved_sink = path.open("a", encoding="utf-8")
            close_on_remove = True

        isatty = getattr(resolved_sink, "isatty", None)
        auto_colorize = bool(callable(isatty) and isatty())
        colorize = auto_colorize if colorize_opt is None else bool(colorize_opt)

        with self._core.lock:
            sink_id = self._core.next_id
            self._core.next_id += 1
            self._core.sinks[sink_id] = _SinkEntry(
                sink=resolved_sink,
                level_no=level_no,
                raw=raw,
                format_string=fmt,
                filter_func=filter_func,
                colorize=colorize,
                close_on_remove=close_on_remove,
            )
            return sink_id

    def remove(self, handler_id: Optional[int] = None) -> None:
        """Remove one sink by ID, or remove all sinks when no ID is provided."""
        with self._core.lock:
            sink_ids = (
                list(self._core.sinks.keys()) if handler_id is None else [handler_id]
            )
            entries = [self._core.sinks.pop(sink_id, None) for sink_id in sink_ids]
        for entry in entries:
            if entry and entry.close_on_remove:
                try:
                    entry.sink.close()
                except OSError as error:
                    _FALLBACK_LOGGER.warning("Could not close log sink: %s", error)

    def flush(self) -> None:
        """Flush all registered sinks that support flushing."""
        with self._core.lock:
            entries = list(self._core.sinks.values())
        for entry in entries:
            try:
                if hasattr(entry.sink, "flush"):
                    entry.sink.flush()
            except OSError as error:
                _FALLBACK_LOGGER.warning("Could not flush log sink: %s", error)

    def bind(self, **kwargs: Any) -> "StructlogAdapter":
        """Return a new logger with additional bound context."""
        return StructlogAdapter(
            name=self._name,
            core=self._core,
            bound_extra={**self._bound_extra, **kwargs},
        )

    @contextmanager
    def contextualize(self, **kwargs: Any) -> Iterator["StructlogAdapter"]:
        """Yield a logger with temporary context values."""
        yield self.bind(**kwargs)

    def set_min_level(self, level: Any) -> None:
        """Set the global minimum log level for this adapter."""
        with self._core.lock:
            self._core.min_level_no = _LEVELS[self._normalize_level_name(level)]

    def get_min_level(self) -> str:
        """Return the current global minimum log level name."""
        with self._core.lock:
            level_no = self._core.min_level_no
        return next(
            (name for name, value in _LEVELS.items() if value == level_no), "INFO"
        )

    def set_component_level(self, component: str, level: Any) -> None:
        """Override the minimum log level for one component."""
        with self._core.lock:
            self._core.component_levels[str(component)] = _LEVELS[
                self._normalize_level_name(level)
            ]

    def clear_component_level(self, component: str) -> None:
        """Remove a component-specific log level override."""
        with self._core.lock:
            self._core.component_levels.pop(str(component), None)

    def clear_all_component_levels(self) -> None:
        """Remove all component-specific log level overrides."""
        with self._core.lock:
            self._core.component_levels.clear()

    def trace(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a TRACE-level log message."""
        self._emit("TRACE", message, *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a DEBUG-level log message."""
        self._emit("DEBUG", message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit an INFO-level log message."""
        self._emit("INFO", message, *args, **kwargs)

    def success(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a SUCCESS-level log message."""
        self._emit("SUCCESS", message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a WARNING-level log message."""
        self._emit("WARNING", message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit an ERROR-level log message."""
        self._emit("ERROR", message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a CRITICAL-level log message."""
        self._emit("CRITICAL", message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit an ERROR-level log message with exception information."""
        kwargs.setdefault("exc_info", True)
        self._emit("ERROR", message, *args, **kwargs)

    def log(self, level: Any, message: str, *args: Any, **kwargs: Any) -> None:
        """Emit a log message at the provided level name or number."""
        self._emit(self._normalize_level_name(level), message, *args, **kwargs)

    def _emit(self, level_name: str, message: str, *args: Any, **kwargs: Any) -> None:
        try:
            extra = kwargs.pop("extra", None) or {}
            exc_info = kwargs.pop("exc_info", None)
            format_kwargs = kwargs
            caller = self._caller_meta(depth=3)
            message_text = self._format_message(message, args, format_kwargs)
            safe_extra = self._ensure_context_ids(
                _safe_redact_mapping({**self._bound_extra, **format_kwargs, **extra})
            )
            safe_message = _safe_redact_text(message_text)
            normalized_level = self._normalize_level_name(level_name)
            component = str(safe_extra.get("component") or self._name)

            if not self._should_log(component, _LEVELS[normalized_level]):
                return

            if _HAS_STRUCTLOG:
                event = {
                    "event": safe_message,
                    "logger": self._name,
                    "level": normalized_level.lower(),
                    "extra": safe_extra,
                    "file": caller["file"],
                    "function": caller["function"],
                    "line": caller["line"],
                    "correlation_id": safe_extra["correlation_id"],
                    "run_id": safe_extra["run_id"],
                    "trace_id": safe_extra["trace_id"],
                }
                if exc_info:
                    event["exc_info"] = True
                self._emit_to_structlog(normalized_level, event)
            else:
                self._emit_to_stdlib(
                    normalized_level, safe_message, exc_info=bool(exc_info)
                )

            record = CompatRecord(
                time=datetime.now(timezone.utc),
                level=_CompatLevel(name=normalized_level, no=_LEVELS[normalized_level]),
                message=safe_message,
                name=self._name,
                file=caller["file"],
                function=caller["function"],
                line=caller["line"],
                correlation_id=safe_extra["correlation_id"],
                run_id=safe_extra["run_id"],
                trace_id=safe_extra["trace_id"],
                extra=safe_extra,
            )
            if _WORKER_LOG_QUEUE is not None:
                try:
                    _WORKER_LOG_QUEUE.put_nowait(record)
                except (AttributeError, OSError, RuntimeError, ValueError) as error:
                    _FALLBACK_LOGGER.warning("Could not enqueue log record: %s", error)
            else:
                self._dispatch_to_sinks(record)
        except Exception as error:  # pylint: disable=broad-exception-caught
            _FALLBACK_LOGGER.exception("Logger emission failed: %s", error)

    def _dispatch_to_sinks(self, record: CompatRecord) -> None:
        with self._core.lock:
            entries = list(self._core.sinks.values())
        for entry in entries:
            if record.level.no < entry.level_no:
                continue
            if entry.filter_func is not None:
                try:
                    if not entry.filter_func(record):
                        continue
                except Exception as error:  # pylint: disable=broad-exception-caught
                    _FALLBACK_LOGGER.warning("Log sink filter failed: %s", error)
                    continue
            try:
                if callable(entry.sink):
                    if entry.raw:
                        entry.sink(record)
                    else:
                        entry.sink(
                            self._format_record(
                                record,
                                entry.format_string,
                                entry.colorize,
                            )
                        )
                elif hasattr(entry.sink, "write"):
                    entry.sink.write(
                        self._format_record(
                            record,
                            entry.format_string,
                            entry.colorize,
                        )
                        + "\n"
                    )
                    if hasattr(entry.sink, "flush"):
                        entry.sink.flush()
            except Exception as error:  # pylint: disable=broad-exception-caught
                _FALLBACK_LOGGER.warning("Log sink dispatch failed: %s", error)

    def dispatch_record(self, record: CompatRecord) -> None:
        """Dispatch a queue-provided record to configured sinks."""
        self._dispatch_to_sinks(record)

    def _emit_to_structlog(self, level_name: str, event: Dict[str, Any]) -> None:
        if level_name in {"ERROR", "CRITICAL"}:
            self._logger.error(**event)
        elif level_name == "WARNING":
            self._logger.warning(**event)
        elif level_name in {"DEBUG", "TRACE"}:
            self._logger.debug(**event)
        else:
            self._logger.info(**event)

    def _emit_to_stdlib(
        self, level_name: str, message: str, *, exc_info: bool = False
    ) -> None:
        if level_name in {"ERROR", "CRITICAL"}:
            self._logger.error(message, exc_info=exc_info)
        elif level_name == "WARNING":
            self._logger.warning(message)
        elif level_name in {"DEBUG", "TRACE"}:
            self._logger.debug(message)
        else:
            self._logger.info(message)

    def _should_log(self, component: str, level_no: int) -> bool:
        with self._core.lock:
            threshold = self._core.component_levels.get(
                component, self._core.min_level_no
            )
        return level_no >= threshold

    @staticmethod
    def _format_message(
        message: str, args: tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> str:
        if not args and not kwargs:
            return str(message)
        message_text = str(message)
        if args:
            try:
                return message_text % args
            except (TypeError, ValueError):
                pass
        try:
            return message_text.format(*args, **kwargs)
        except (IndexError, KeyError, ValueError):
            suffix = " ".join(
                [str(arg) for arg in args]
                + [f"{key}={value}" for key, value in kwargs.items()]
            )
            return f"{message_text} {suffix}".strip()

    @staticmethod
    def _format_record(
        record: CompatRecord, fmt: Optional[str], colorize: bool = False
    ) -> str:
        template = fmt or "{time} | {level} | {message}"
        level_text = (
            StructlogAdapter._colorize_level(record.level.name)
            if colorize
            else record.level.name
        )
        payload = {
            "time": record.time.strftime("%Y-%m-%d %H:%M:%S"),
            "level": level_text,
            "level_plain": record.level.name,
            "message": record.message,
            "name": record.name,
            "file": record.file,
            "function": record.function,
            "line": record.line,
            "correlation_id": record.correlation_id,
            "run_id": record.run_id,
            "trace_id": record.trace_id,
            "extra": record.extra,
        }
        try:
            return template.format(**payload)
        except (IndexError, KeyError, ValueError):
            return f"{payload['time']} | {payload['level']} | {payload['message']}"

    @staticmethod
    def _colorize_level(level_name: str) -> str:
        colors = {
            "TRACE": "\033[36m",
            "DEBUG": "\033[34m",
            "INFO": "\033[32m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[33m",
            "ERROR": "\033[31m",
            "CRITICAL": "\033[91m",
        }
        color = colors.get(level_name.upper())
        return f"{color}{level_name}\033[0m" if color else level_name

    @staticmethod
    def _caller_meta(depth: int = 3) -> Dict[str, Any]:
        frame = inspect.currentframe()
        for _ in range(depth):
            if frame is None:
                break
            frame = frame.f_back
        if frame is None:
            return {"file": "<unknown>", "function": "<unknown>", "line": 0}
        return {
            "file": frame.f_globals.get("__name__")
            or Path(frame.f_code.co_filename).stem,
            "function": frame.f_code.co_name,
            "line": int(frame.f_lineno),
        }

    @staticmethod
    def _normalize_level_name(level: Any) -> str:
        if isinstance(level, int):
            for name, value in _LEVELS.items():
                if value == level:
                    return name
            if level <= 10:
                return "DEBUG"
            if level <= 20:
                return "INFO"
            if level <= 30:
                return "WARNING"
            if level <= 40:
                return "ERROR"
            return "CRITICAL"
        name = _LEVEL_ALIASES.get(str(level).upper(), str(level).upper())
        return name if name in _LEVELS else "INFO"

    @staticmethod
    def _ensure_context_ids(extra: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(extra)
        for key in _CONTEXT_ID_KEYS:
            out[key] = "" if out.get(key) is None else str(out.get(key))
        return out


Logger = StructlogAdapter
logger = StructlogAdapter()


def _is_access_record(record: CompatRecord) -> bool:
    """Return True when a log record should be routed to the access log."""
    component = str(record.extra.get("component", "")).lower()
    access_keys = ("method", "path", "status_code", "remote_addr")
    return "access" in component or any(key in record.extra for key in access_keys)


def configure_default_file_sinks(
    log_dir: Path | str = DEFAULT_LOG_DIR,
    *,
    log_instance: Optional[StructlogAdapter] = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> None:
    """Configure standard HaruQuant log files explicitly.

    Args:
        log_dir: Directory where log files should be written.
        log_instance: Optional logger instance. Defaults to module logger.
        max_bytes: Maximum size per active log file before rotation.
        backup_count: Number of rotated backups to retain per log file.

    Raises:
        ValueError: If max_bytes or backup_count are not positive.
    """
    global _DEFAULT_FILE_SINKS_CONFIGURED  # pylint: disable=global-statement
    if max_bytes <= 0:
        raise ValueError("max_bytes must be greater than zero.")
    if backup_count <= 0:
        raise ValueError("backup_count must be greater than zero.")
    if _DEFAULT_FILE_SINKS_CONFIGURED:
        return

    sink_owner = log_instance or logger
    directory = Path(log_dir)
    directory.mkdir(parents=True, exist_ok=True)
    sink_owner.add(
        _SizeAndTimeRotatingFileSink(
            directory / "app.log", max_bytes=max_bytes, backup_count=backup_count
        ),
        level="INFO",
        close_on_remove=True,
    )
    sink_owner.add(
        _SizeAndTimeRotatingFileSink(
            directory / "debug.log", max_bytes=max_bytes, backup_count=backup_count
        ),
        level="DEBUG",
        close_on_remove=True,
    )
    sink_owner.add(
        _SizeAndTimeRotatingFileSink(
            directory / "errors.log", max_bytes=max_bytes, backup_count=backup_count
        ),
        level="ERROR",
        close_on_remove=True,
    )
    sink_owner.add(
        _SizeAndTimeRotatingFileSink(
            directory / "access.log", max_bytes=max_bytes, backup_count=backup_count
        ),
        level="INFO",
        filter=_is_access_record,
        close_on_remove=True,
    )
    _DEFAULT_FILE_SINKS_CONFIGURED = True


def _build_tool_metadata(
    tool_name: str, request_id: Optional[str], execution_ms: float
) -> Dict[str, Any]:
    """Build standard HaruQuantAI tool response metadata."""
    return {
        "tool_name": tool_name,
        "tool_version": TOOL_VERSION,
        "tool_category": TOOL_CATEGORY,
        "tool_risk_level": TOOL_RISK_LEVEL,
        "request_id": request_id,
        "execution_ms": execution_ms,
        "read_only": READ_ONLY,
        "writes_file": WRITES_FILE,
        "modifies_database": MODIFIES_DATABASE,
        "places_trade": PLACES_TRADE,
        "requires_network": REQUIRES_NETWORK,
    }


def _build_tool_response(
    *,
    tool_name: str,
    status: str,
    message: str,
    data: Any,
    error: Optional[Dict[str, str]],
    request_id: Optional[str],
    started_at: float,
) -> Dict[str, Any]:
    """Build a standard HaruQuantAI tool response."""
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return {
        "status": status,
        "message": message,
        "data": data,
        "error": error,
        "metadata": _build_tool_metadata(tool_name, request_id, execution_ms),
    }


def _queue_has_method(queue: Any, method_name: str) -> bool:
    """Return True when a queue-like object has the required callable method."""
    return callable(getattr(queue, method_name, None))


def _init_worker_logger(queue: Any) -> None:
    """Route current process log records through a multiprocessing queue."""
    global _WORKER_LOG_QUEUE  # pylint: disable=global-statement
    _WORKER_LOG_QUEUE = queue


def init_worker_logger(queue: Any, request_id: Optional[str] = None) -> Dict[str, Any]:
    """Initialize a worker process logger for multiprocessing workflows.

    Use this AI tool when an agent or workflow starts worker processes and wants
    logs from those workers to be routed to the main process through a shared
    queue. The queue must support `put_nowait`.

    Args:
        queue: Multiprocessing-compatible queue used for log records.
        request_id: Optional workflow/request ID for traceability.

    Returns:
        Standard HaruQuantAI tool response containing status, message, data,
        error, and metadata.

    Error Cases:
        INVALID_INPUT: The queue is missing or does not support put_nowait.
        TOOL_EXECUTION_FAILED: An unexpected initialization error occurred.

    Side Effects:
        Updates process-local logging state so future log records are queued.
    """
    tool_name = "init_worker_logger"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    if queue is None or not _queue_has_method(queue, "put_nowait"):
        logger.warning(
            "%s validation failed | request_id=%s | reason=invalid_queue",
            tool_name,
            request_id,
        )
        return _build_tool_response(
            tool_name=tool_name,
            status="error",
            message="A multiprocessing queue with put_nowait is required.",
            data=None,
            error={
                "code": "INVALID_INPUT",
                "details": "queue must provide a callable put_nowait method.",
            },
            request_id=request_id,
            started_at=started_at,
        )

    try:
        _init_worker_logger(queue)
        logger.info("%s completed successfully | request_id=%s", tool_name, request_id)
        return _build_tool_response(
            tool_name=tool_name,
            status="success",
            message="Worker logger initialized.",
            data=True,
            error=None,
            request_id=request_id,
            started_at=started_at,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _build_tool_response(
            tool_name=tool_name,
            status="error",
            message="Worker logger initialization failed.",
            data=None,
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(exc)},
            request_id=request_id,
            started_at=started_at,
        )


def _configure_multiprocess_listener(
    queue: Any, log_instance: Optional[StructlogAdapter] = None
) -> None:
    """Start a daemon thread that drains log records from a queue."""
    global _QUEUE_LISTENER_RUNNING  # pylint: disable=global-statement
    with _QUEUE_LISTENER_LOCK:
        if _QUEUE_LISTENER_RUNNING:
            return
        sink_owner = log_instance or logger

        def _listener_loop() -> None:
            while True:
                try:
                    record = queue.get(timeout=0.5)
                    if record is None:
                        break
                    if isinstance(record, CompatRecord):
                        sink_owner.dispatch_record(record)
                    else:
                        _FALLBACK_LOGGER.warning(
                            "Ignoring unsupported log queue item: %r", record
                        )
                except TimeoutError:
                    continue
                except Exception as error:  # pylint: disable=broad-exception-caught
                    if error.__class__.__name__ == "Empty":
                        continue
                    if isinstance(error, (EOFError, OSError)):
                        break
                    if "handle is closed" in str(error).lower():
                        break
                    _FALLBACK_LOGGER.warning("Log queue listener error: %s", error)
            with _QUEUE_LISTENER_LOCK:
                global _QUEUE_LISTENER_RUNNING  # pylint: disable=global-statement
                _QUEUE_LISTENER_RUNNING = False

        thread = threading.Thread(
            target=_listener_loop, name="haruquant-log-queue-listener", daemon=True
        )
        thread.start()
        _QUEUE_LISTENER_RUNNING = True


def configure_multiprocess_listener(
    queue: Any,
    log_instance: Any = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Start a main-process listener for worker log records.

    Use this AI tool in the main process before running multiprocessing workers.
    The listener drains a queue and dispatches `CompatRecord` values through the
    configured logger sinks. The queue must support `get`.

    Args:
        queue: Multiprocessing-compatible queue used for log records.
        log_instance: Optional logger instance that owns the destination sinks.
        request_id: Optional workflow/request ID for traceability.

    Returns:
        Standard HaruQuantAI tool response containing status, message, data,
        error, and metadata.

    Error Cases:
        INVALID_INPUT: The queue is missing, does not support get, or the logger
            override is not a StructlogAdapter.
        TOOL_EXECUTION_FAILED: An unexpected listener configuration error occurred.

    Side Effects:
        Starts a daemon thread in the current process. The thread may write to
        configured log sinks, including files.
    """
    tool_name = "configure_multiprocess_listener"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    if queue is None or not _queue_has_method(queue, "get"):
        logger.warning(
            "%s validation failed | request_id=%s | reason=invalid_queue",
            tool_name,
            request_id,
        )
        return _build_tool_response(
            tool_name=tool_name,
            status="error",
            message="A multiprocessing queue with get is required.",
            data=None,
            error={
                "code": "INVALID_INPUT",
                "details": "queue must provide a callable get method.",
            },
            request_id=request_id,
            started_at=started_at,
        )
    if log_instance is not None and not isinstance(log_instance, StructlogAdapter):
        logger.warning(
            "%s validation failed | request_id=%s | reason=invalid_logger",
            tool_name,
            request_id,
        )
        return _build_tool_response(
            tool_name=tool_name,
            status="error",
            message="log_instance must be a StructlogAdapter when provided.",
            data=None,
            error={
                "code": "INVALID_INPUT",
                "details": "log_instance must be None or StructlogAdapter.",
            },
            request_id=request_id,
            started_at=started_at,
        )

    try:
        _configure_multiprocess_listener(queue, log_instance)
        logger.info("%s completed successfully | request_id=%s", tool_name, request_id)
        return _build_tool_response(
            tool_name=tool_name,
            status="success",
            message="Multiprocess logging listener configured.",
            data=True,
            error=None,
            request_id=request_id,
            started_at=started_at,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _build_tool_response(
            tool_name=tool_name,
            status="error",
            message="Multiprocess listener configuration failed.",
            data=None,
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(exc)},
            request_id=request_id,
            started_at=started_at,
        )


__all__ = [
    "StructlogAdapter",
    "Logger",
    "CompatRecord",
    "logger",
    "configure_default_file_sinks",
    "init_worker_logger",
    "configure_multiprocess_listener",
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
    "DEFAULT_LEVELS",
]
