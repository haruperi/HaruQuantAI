# pylint: disable=broad-exception-caught,global-statement,unidiomatic-typecheck,protected-access
# cspell:ignore NONFINITE CREAT WRONLY timespec
"""Bounded sanitized logging, explicit lifecycle, and asynchronous sinks.

Import and logger construction perform no I/O, thread startup, logger registration,
or standard-library logging configuration. Only `configure_logging()` owns sinks.

Key Design Principles:
- Zero Import Overhead: Importing this module or calling `get_logger()` allocates
  only an inert facade. No threads are spawned, no files opened, and no root
  logging handlers are hijacked.
- Asynchronous Non-Blocking I/O: Log events are sanitized, bounded, and queued
  in memory before returning to the caller. A dedicated daemon thread handles
  all disk and console writes.
- Automatic Secret Redaction: Sensitive credential patterns (Bearer tokens, API
  keys, passwords, connection strings, private keys) and caller-specified
  secrets are automatically masked as `[REDACTED]` before writing.
- Crash-Resilient ZIP Rotation: Log files are compressed into ZIP archives before
  truncation. If rotation encounters an OS error, active records remain safely
  preserved on disk without truncation.
- Contextual Correlation: Supports task/thread-local context propagation using
  `bind_correlation()` and `contextvars`.
"""

from __future__ import annotations

import contextvars
import heapq
import itertools
import json
import math
import os
import queue
import re
import shutil
import sys
import threading
import time
import zipfile
from collections import deque
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO, cast
from uuid import uuid4

_LEVELS = {10: "DEBUG", 20: "INFO", 30: "WARNING", 40: "ERROR", 50: "CRITICAL"}
_COLORS = {
    "DEBUG": "36",
    "INFO": "32",
    "WARNING": "33",
    "ERROR": "31",
    "CRITICAL": "1;31",
}
_SENSITIVE = re.compile(
    r"password|passwd|secret|token|api.?key|credential|authorization|cookie|"
    r"private.?key|passphrase|signature",
    re.IGNORECASE,
)
_CREDENTIAL = re.compile(
    r"(?i)(?:bearer|basic)\s+[^\s,;]+|"
    r"(?:password|passwd|secret|token|api[_-]?key|credential|passphrase)"
    r"\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;&]+)|"
    r"[a-z][a-z0-9+.-]*://[^\s/@]+:[^\s/@]+@|"
    r"\b(?:sk|pk)[_-][a-zA-Z0-9_-]{12,}|"
    r"\beyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"
)
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f\u2028\u2029\u202a-\u202e\u2066-\u2069]")
_CORRELATION: contextvars.ContextVar[dict[str, object] | None] = contextvars.ContextVar(
    "application_log_correlation", default=None
)
_IN_SINK: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "log_sink_active", default=False
)
# Inert synchronization primitives; no held locks or started threads at import.
_STATE_LOCK = threading.RLock()
_CONFIG_LOCK = threading.RLock()


class _ActiveLoggingState:
    """Thread-safe mutable container tracking the active logging generation."""

    active: LoggingHandle | None = None


_ACTIVE_STATE = _ActiveLoggingState()
_TEXT_LIMIT = 2048
_NODE_LIMIT = 128
_RECORD_LIMIT = 16384
_REDACTED = "[REDACTED]"


def _text(value: str, secrets: tuple[str, ...] = ()) -> str:
    """Bound work before regex processing; never expose oversized fragments."""
    if len(value) > _TEXT_LIMIT:
        return "[OVERSIZED TEXT]"
    if secrets:
        pattern = "|".join(
            re.escape(secret) for secret in sorted(secrets, key=len, reverse=True)
        )
        # One pass: replacement markers must never be redacted/expanded again.
        value = re.sub(pattern, _REDACTED, value)
    value = _CREDENTIAL.sub(_REDACTED, value)
    if "-----BEGIN " in value:
        return _REDACTED
    value = _CONTROL.sub(lambda match: f"\\u{ord(match[0]):04x}", value)
    return value if len(value) <= _TEXT_LIMIT else "[OVERSIZED TEXT]"


def sanitize(value: object, *, secrets: tuple[str, ...] = ()) -> object:
    """Copy safe builtins with bounded depth, breadth, and total nodes.

    Unknown objects are replaced without calling repr, str, iter, or properties.
    Sensitive keys are removed before traversing values; cycles are marked.
    """
    remaining = _NODE_LIMIT
    ancestors: set[int] = set()

    def visit(item: object, depth: int) -> object:
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > 6:
            return "[LIMIT]"
        if item is None or type(item) is bool:
            return item
        if type(item) is str:
            return _text(item, secrets)
        if type(item) is int:
            return item if item.bit_length() <= 64 else "[LARGE INTEGER]"
        if type(item) is float:
            return item if math.isfinite(item) else "[NONFINITE]"
        if type(item) not in (dict, list, tuple):
            return "[UNSUPPORTED OBJECT]"
        item_id = id(item)
        if item_id in ancestors:
            return "[CYCLE]"
        ancestors.add(item_id)
        try:
            if type(item) is dict:
                result: dict[str, object] = {}
                mapping = cast("dict[object, object]", item)
                for key, child in itertools.islice(mapping.items(), 32):
                    if remaining <= 0:
                        break
                    if type(key) is not str:
                        continue
                    safe_key = _text(key, secrets)
                    result[safe_key] = (
                        _REDACTED
                        if len(key) > _TEXT_LIMIT or _SENSITIVE.search(key)
                        else visit(child, depth + 1)
                    )
                if len(mapping) > len(result):
                    result["_truncated"] = True
                return result
            sequence = cast("list[object] | tuple[object, ...]", item)
            output: list[object] = []
            for child in itertools.islice(sequence, 32):
                if remaining <= 0:
                    break
                output.append(visit(child, depth + 1))
            if len(sequence) > len(output):
                output.append("[TRUNCATED]")
            return output
        finally:
            ancestors.remove(item_id)

    try:
        return visit(value, 0)
    except RuntimeError, RecursionError:
        return "[UNSTABLE CONTEXT]"


def _fields(value: object, secrets: tuple[str, ...] = ()) -> dict[str, object]:
    """Produce a bounded mapping retaining no caller-owned containers."""
    safe = sanitize(value, secrets=secrets)
    return cast("dict[str, object]", safe) if isinstance(safe, dict) else {}


@contextmanager
def bind_correlation(**context: object) -> Generator[None]:
    """Bind task/thread-local fields and restore them on every exit.

    Async tasks inherit snapshots. Use copy_context().run for propagation to
    manual threads; asyncio.to_thread propagates the current context.
    """
    token = _CORRELATION.set(
        _fields({**(_CORRELATION.get() or {}), **_fields(context)})
    )
    try:
        yield
    finally:
        _CORRELATION.reset(token)


def get_correlation_context() -> dict[str, object]:
    """Return a defensive sanitized copy of current correlation fields."""
    return _fields(_CORRELATION.get() or {})


@dataclass(frozen=True)
class LoggingConfig:
    """Finite budgets and sink policy; file paths are bootstrap-owned.

    Queue saturation drops newest sink records; diagnostics retain the newest
    attempts independently. Retention deletes only recognized owned ZIP archives.
    """

    namespace: str = "app"
    level: int = 20
    console: bool = True
    colorize: bool = True
    log_directory: Path | None = Path("data/logs")
    purposes: tuple[str, ...] = ("application", "errors", "audit")
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 10
    retention_days: int = 30
    queue_capacity: int = 1024
    capture_capacity: int = 256
    secrets: tuple[str, ...] = field(default=(), repr=False)

    def validate(self) -> None:
        """Reject invalid and excessive budgets before preparing resources."""
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,63}", self.namespace):
            raise ValueError("Invalid logging namespace")
        if self.level not in _LEVELS:
            raise ValueError("Unsupported logging level")
        for number, minimum, maximum in (
            (self.max_bytes, 256, 1024 * 1024 * 1024),
            (self.backup_count, 1, 1000),
            (self.retention_days, 1, 3650),
            (self.queue_capacity, 1, 65536),
            (self.capture_capacity, 1, 65536),
        ):
            if type(number) is not int or not minimum <= number <= maximum:
                raise ValueError("Logging budget outside supported bounds")
        if (
            type(self.purposes) is not tuple
            or not 2 <= len(self.purposes) <= 16
            or len(set(self.purposes)) != len(self.purposes)
            or not {"application", "errors"} <= set(self.purposes)
            or any(not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", p) for p in self.purposes)
        ):
            raise ValueError("Invalid purpose routes")
        if (
            type(self.secrets) is not tuple
            or len(self.secrets) > 64
            or any(
                type(secret) is not str or not 1 <= len(secret) <= _TEXT_LIMIT
                for secret in self.secrets
            )
        ):
            raise ValueError("Invalid secret redaction registry")


class _FileSink:
    """Single-writer JSONL sink with archive-before-truncate rotation."""

    def __init__(self, directory: Path, purpose: str, config: LoggingConfig) -> None:
        """Initialize a file sink for a specific purpose channel.

        Args:
            directory: Directory where the log file is placed.
            purpose: Purpose channel name (e.g., 'application', 'errors').
            config: Logging configuration defining rotation and retention policies.

        Raises:
            ValueError: If the target file is a symbolic link.
        """
        self.path = directory / f"{purpose}.jsonl"
        if self.path.is_symlink():
            raise ValueError("Log file must not be a symbolic link")
        self.config = config
        self.stream = self.path.open("a", encoding="utf-8", newline="\n")
        try:
            self.size = self.path.stat().st_size
        except BaseException:
            self.stream.close()
            raise
        self.last_prune = 0.0

    def write(self, line: str) -> None:
        """Rotate on size and periodically expire only recognized archives."""
        size = len(line.encode("utf-8")) + 1
        if self.size and self.size + size > self.config.max_bytes:
            self._rotate()
        self.stream.write(line + "\n")
        self.stream.flush()
        self.size += size
        if time.monotonic() - self.last_prune >= 60:
            self.prune()

    def _rotate(self) -> None:
        """Publish a complete ZIP before clearing active bytes; preserve on error."""
        self.stream.flush()
        archive = self.path.with_name(
            f"{self.path.name}.{time.time_ns()}-{uuid4().hex}.zip"
        )
        staging = archive.with_suffix(".zip.tmp")
        created = False
        try:
            with staging.open("xb") as archive_stream:
                created = True
                with zipfile.ZipFile(
                    archive_stream, "w", compression=zipfile.ZIP_DEFLATED
                ) as bundle:
                    with (
                        self.path.open("rb") as source,
                        bundle.open(self.path.name, "w") as target,
                    ):
                        shutil.copyfileobj(source, target, length=64 * 1024)
                archive_stream.flush()
                os.fsync(archive_stream.fileno())
            if archive.exists():
                raise FileExistsError("Archive identity collision")
            staging.replace(archive)
        except BaseException:
            if created:
                staging.unlink(missing_ok=True)
            raise
        # A crash here may duplicate records but does not erase their only copy.
        self.stream.seek(0)
        self.stream.truncate(0)
        self.size = 0
        self.prune()

    def prune(self) -> None:
        """Apply age/count policy without touching active or unrelated files."""
        pattern = re.compile(re.escape(self.path.name) + r"\.\d+-[0-9a-f]{32}\.zip")
        cutoff = time.time() - self.config.retention_days * 86400
        keep: list[tuple[float, str]] = []
        # scandir streams directory entries; heap memory is bounded by backup_count.
        with os.scandir(self.path.parent) as entries:
            for entry in entries:
                if not pattern.fullmatch(entry.name) or not entry.is_file(
                    follow_symlinks=False
                ):
                    continue
                modified = entry.stat(follow_symlinks=False).st_mtime
                if modified < cutoff:
                    Path(entry.path).unlink()
                    continue
                heapq.heappush(keep, (modified, entry.path))
                if len(keep) > self.config.backup_count:
                    _, expired = heapq.heappop(keep)
                    Path(expired).unlink()
        self.last_prune = time.monotonic()

    def close(self) -> None:
        """Close only the owned stream."""
        self.stream.close()


def _console(record: dict[str, Any], colorize: bool) -> str:
    """Format sanitized data using UTC and a single physical line."""
    timestamp = record["timestamp"].replace("T", " ").removesuffix("Z")
    level = record["level"]
    message = record["message"]
    if colorize:
        color = _COLORS[level]
        level = f"\x1b[{color}m{level}\x1b[0m"
        message = f"\x1b[{color}m{message}\x1b[0m"
    caller = record["caller"]
    base = (
        f"{timestamp} | {level} | {record['module']}:"
        f"{caller['function']}:{caller['line']}"
        f" - {message}"
    )
    if record.get("context"):
        context = json.dumps(
            record["context"], ensure_ascii=True, separators=(",", ":")
        )
        return f"{base} | {context}"
    return base


class LoggingHandle:
    """Own one writer generation; expose bounded diagnostics and health."""

    def __init__(self, config: LoggingConfig, stream: TextIO | None = None) -> None:
        """Initialize a logging handle generation.

        Args:
            config: Validated configuration governing this generation.
            stream: Target text stream for console output (default: sys.stderr).
        """
        self.config = config
        self._stream = stream if stream is not None else sys.stderr
        self._queue: queue.Queue[str] = queue.Queue(config.queue_capacity)
        self._capture: deque[str] = deque(maxlen=config.capture_capacity)
        self._condition = threading.Condition()
        self._stop = threading.Event()
        self._activate = threading.Event()
        self._thread: threading.Thread | None = None
        self._files: dict[str, _FileSink] = {}
        self._lock_path: Path | None = None
        self._lock_fd: int | None = None
        self.previous: LoggingHandle | None = None
        self._accepting = True
        self._closed = False
        self._accepted = 0
        self._completed = 0
        self._dropped = 0
        self._sink_failures = 0
        self._last_error: str | None = None

    def prepare(self) -> None:
        """Acquire sinks without publishing this generation or pruning history."""
        try:
            directory = self.config.log_directory
            if directory is not None:
                directory.mkdir(parents=True, exist_ok=True)
                self._lock_path = directory / ".logging.lock"
                self._lock_fd = os.open(
                    self._lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
                )
                for purpose in self.config.purposes:
                    self._files[purpose] = _FileSink(directory, purpose, self.config)
            self._thread = threading.Thread(
                target=self._run,
                name=f"{self.config.namespace}-log-writer",
                daemon=True,
            )
            self._thread.start()
        except BaseException:
            self._release_files()
            raise

    def activate(self) -> None:
        """Signal writer thread that initialization is complete."""
        self._activate.set()

    def record_error(self, stage: str) -> None:
        """Store bounded codes; never recursively log sink exceptions."""
        with self._condition:
            self._sink_failures += 1
            self._last_error = stage

    def _release_files(self) -> None:
        """Attempt all closes; never remove log files or directories."""
        for sink in self._files.values():
            try:
                sink.close()
            except Exception:
                self.record_error("file_close_failed")
        self._files.clear()
        if self._lock_fd is not None:
            try:
                os.close(self._lock_fd)
                self._lock_fd = None
                if self._lock_path is not None:
                    self._lock_path.unlink(missing_ok=True)
            except OSError:
                self.record_error("directory_lock_cleanup_failed")

    def _run(self) -> None:
        """Drain immutable sanitized records; all sink work stays on this thread."""
        self._activate.wait()
        _IN_SINK.set(True)
        try:
            while not self._stop.is_set() or not self._queue.empty():
                try:
                    line = self._queue.get(timeout=0.05)
                except queue.Empty:
                    for retained_sink in self._files.values():
                        if time.monotonic() - retained_sink.last_prune >= 60:
                            try:
                                retained_sink.prune()
                            except Exception:
                                retained_sink.last_prune = time.monotonic()
                                self.record_error("archive_retention_failed")
                    continue
                try:
                    record = json.loads(line)
                    if self.config.console:
                        try:
                            self._stream.write(
                                _console(record, self.config.colorize) + "\n"
                            )
                            self._stream.flush()
                        except Exception:
                            self.record_error("console_write_failed")
                    sink = self._files.get(record["purpose"])
                    if sink is not None:
                        try:
                            sink.write(line)
                        except Exception:
                            self.record_error("file_write_failed")
                finally:
                    self._queue.task_done()
                    with self._condition:
                        self._completed += 1
                        self._condition.notify_all()
        finally:
            self._release_files()

    def submit(self, record: dict[str, Any]) -> None:
        """Capture immediately; enqueue without waiting for sink capacity."""
        line = json.dumps(
            record, ensure_ascii=True, allow_nan=False, separators=(",", ":")
        )
        if len(line) > _RECORD_LIMIT:
            record["context"] = {"_truncated": True}
            record["message"] = "[RECORD SIZE LIMIT]"
            record["module"] = record["module"][:128]
            record["caller"]["function"] = record["caller"]["function"][:128]
            line = json.dumps(record, ensure_ascii=True, separators=(",", ":"))
        with self._condition:
            if not self._accepting:
                self._dropped += 1
                return
            self._capture.append(line)
            try:
                self._queue.put_nowait(line)
                self._accepted += 1
            except queue.Full:
                self._dropped += 1

    def snapshot(self) -> list[dict[str, Any]]:
        """Return defensive JSON-safe copies of recent records, including drops."""
        with self._condition:
            lines = tuple(self._capture)
        return [json.loads(line) for line in lines]

    def health(self) -> dict[str, int | str | bool | None]:
        """Report queue loss, sink failures, and progress without raw errors."""
        with self._condition:
            return {
                "accepted": self._accepted,
                "completed": self._completed,
                "dropped": self._dropped,
                "sink_failures": self._sink_failures,
                "last_error": self._last_error,
                "closed": self._closed,
                "writer_alive": self._thread is not None and self._thread.is_alive(),
            }

    def flush(self, timeout: float = 5.0) -> bool:
        """Wait up to timeout for all records accepted before this call."""
        if not math.isfinite(timeout) or timeout < 0:
            raise ValueError("Invalid flush timeout")
        with self._condition:
            target = self._accepted
            return self._condition.wait_for(lambda: self._completed >= target, timeout)

    def close(self, timeout: float = 5.0) -> None:
        """Restore previous generation, drain, and stop without deleting logs.

        A blocked OS sink cannot be force-killed. Timeout raises and leaves the
        daemon writer owning resources until it finishes; retry close later.
        Generations must close in reverse configuration order.
        """
        if not math.isfinite(timeout) or timeout < 0:
            raise ValueError("Invalid close timeout")
        with _CONFIG_LOCK:
            with _STATE_LOCK:
                if not self._closed:
                    if _ACTIVE_STATE.active is not self:
                        raise RuntimeError(
                            "Logging generations must close in reverse order"
                        )
                    _ACTIVE_STATE.active = self.previous
                    with self._condition:
                        self._accepting = False
                        self._closed = True
                    self._stop.set()
            if self._thread is not None:
                self._thread.join(timeout)
                if self._thread.is_alive():
                    raise TimeoutError("Logging writer did not stop before timeout")


@contextmanager
def configure_logging(
    config: LoggingConfig | None = None,
    *,
    namespace: str = "app",
    level: int = 20,
    stream: TextIO | None = None,
) -> Generator[LoggingHandle]:
    """Prepare then atomically activate a generation; restore it on exit.

    Existing stdlib loggers and supplied streams are never modified or closed.
    Explicit config overrides namespace/level convenience arguments.
    """
    selected = (
        config
        if config is not None
        else LoggingConfig(namespace=namespace, level=level)
    )
    selected.validate()
    with _CONFIG_LOCK:
        handle = LoggingHandle(selected, stream)
        handle.prepare()
        with _STATE_LOCK:
            handle.previous, _ACTIVE_STATE.active = _ACTIVE_STATE.active, handle
            handle.activate()
    try:
        yield handle
    finally:
        handle.close()


class BoundLogger:
    """Inert contextual facade; emits nothing until explicitly configured."""

    def __init__(self, name: str, context: dict[str, object] | None = None) -> None:
        """Initialize an immutable bound logger facade.

        Args:
            name: Module or component name identifying log records from this logger.
            context: Optional dictionary of contextual metadata key-value pairs.
        """
        self._name = _text(name)
        self._context = _fields(context or {})

    def bind(self, **context: object) -> BoundLogger:
        """Return an independent logger with bounded sanitized bindings."""
        return BoundLogger(self._name, {**self._context, **_fields(context)})

    def _emit(
        self,
        level: int,
        message: str,
        context: dict[str, object],
        *,
        exception: bool = False,
    ) -> None:
        """Format and submit a log record to the active logging generation.

        Args:
            level: Logging level integer (10, 20, 30, 40, or 50).
            message: Description of the log event.
            context: Additional structured key-value pairs.
            exception: If True, attach sanitized exception type and stack trace.
        """
        with _STATE_LOCK:
            handle = _ACTIVE_STATE.active
        if handle is None or level < handle.config.level:
            return
        if _IN_SINK.get():
            handle.record_error("recursive_log_suppressed")
            return
        secrets = handle.config.secrets
        fields = _fields(
            {
                **self._context,
                **(_CORRELATION.get() or {}),
                **_fields(context, secrets),
            },
            secrets,
        )
        purpose = fields.pop("purpose", "application")
        if purpose not in handle.config.purposes:
            purpose = "application"
        if level >= 40 and purpose == "application":
            purpose = "errors"
        # pylint: disable-next-line=protected-access
        frame = sys._getframe(2)  # pyright: ignore[reportPrivateUsage]
        caller: dict[str, object] = {
            "function": _text(frame.f_code.co_name, secrets),
            "line": frame.f_lineno,
        }
        del frame
        if exception:
            error_type, error, traceback = sys.exc_info()
            frames: list[dict[str, object]] = []
            while traceback is not None and len(frames) < 16:
                frames.append(
                    {
                        "function": _text(traceback.tb_frame.f_code.co_name, secrets),
                        "line": traceback.tb_lineno,
                    }
                )
                traceback = traceback.tb_next
            fields["exception"] = {
                "type": _text(error_type.__name__, secrets) if error_type else None,
                "frames": frames,
            }
            del error, traceback
        record: dict[str, Any] = {
            "schema_version": 1,
            "timestamp": datetime.now(UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": _LEVELS[level],
            "module": _text(self._name, secrets),
            "caller": caller,
            "purpose": purpose,
            "message": sanitize(message, secrets=secrets),
            "context": fields,
        }
        handle.submit(record)

    def debug(self, message: str, **context: object) -> None:
        """Emit a DEBUG event."""
        self._emit(10, message, context)

    def info(self, message: str, **context: object) -> None:
        """Emit an INFO event."""
        self._emit(20, message, context)

    def warning(self, message: str, **context: object) -> None:
        """Emit a WARNING event."""
        self._emit(30, message, context)

    def error(self, message: str, **context: object) -> None:
        """Emit an ERROR event."""
        self._emit(40, message, context)

    def critical(self, message: str, **context: object) -> None:
        """Emit a CRITICAL event."""
        self._emit(50, message, context)

    def exception(self, message: str, **context: object) -> None:
        """Emit ERROR with bounded frame locations, never raw exception text."""
        self._emit(40, message, context, exception=True)


def get_logger(name: str = "app") -> BoundLogger:
    """Create an inert facade without touching stdlib logger state."""
    return BoundLogger(name)


__all__ = (
    "BoundLogger",
    "LoggingConfig",
    "LoggingHandle",
    "bind_correlation",
    "configure_logging",
    "get_correlation_context",
    "get_logger",
    "sanitize",
)
