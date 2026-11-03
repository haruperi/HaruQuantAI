"""Host application logging, secret redaction, diagnostics, and CLI redirection.

Description:
    Provides thread-safe, non-blocking asynchronous logging with a rotating
    file handler and console output. Incorporates sensitive data redaction to
    prevent credential leakage, sliding-window duplicate log message
    suppression, dynamic debug logging activation via configuration settings,
    system startup diagnostic telemetry reporting, and CLI output redirection.

Purpose:
    FEAT-HOST-LOGGING: Unified host logging, diagnostics, secret redaction,
    and CLI redirection.

Key Capabilities:
    - FR-HOST-LOGGING-ASYNC-QUEUE: Async worker (setup_logging -> INFO).
    - FR-HOST-LOGGING-ROTATION-RECOVERY: File lock retry (doRollover -> INFO).
    - FR-HOST-LOGGING-SENSITIVE-REDACTION: Redact secrets (filter -> DEBUG).
    - FR-HOST-LOGGING-DUPLICATE-SUPPRESSION: Throttle duplicates (filter -> DEBUG).
    - FR-HOST-LOGGING-DEBUG-TOGGLE: Debug level switch (activate_debug_logging -> INFO).
    - FR-HOST-LOGGING-STARTUP-DIAGNOSTICS: Telemetry (emit_startup_diagnostics -> INFO).
    - FR-HOST-LOGGING-CLI-REDIRECTION: CLI stream redirection (log -> INFO).

Python API Usage:
    ```python
    from app.core.host.logging import (
        activate_debug_logging,
        emit_startup_diagnostics,
        get_logger,
        setup_logging,
    )

    logger = get_logger(__name__)
    logger.info("Application starting")
    emit_startup_diagnostics(app_version="1.0.0")
    ```

CLI Usage:
    ```bash
    uv run python -m app.core.host.logging
    ```
"""

from __future__ import annotations

import atexit
import copy
import logging
import logging.handlers
import os
import platform
import queue
import re
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, TextIO, override

_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)s | "
    "%(module)s:%(funcName)s:%(lineno)d - %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 10 * 1024 * 1024
_RETENTION_SECONDS = 30 * 24 * 60 * 60
_RETRY_ATTEMPTS = 5
_LOCK = threading.RLock()
_listener: logging.handlers.QueueListener | None = None
_queue_handler: logging.Handler | None = None
_previous_level = logging.WARNING
_CLI_SEPARATOR = "-" * 50

_NOISY_LOGGERS: tuple[str, ...] = (
    "urllib3",
    "httpx",
    "httpcore",
    "asyncio",
    "uvicorn.access",
)

_SENSITIVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9\-._~+/]+=*"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(?i)\b(basic\s+)[A-Za-z0-9+/]+=*"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(
            r"""(?i)(["']?(?:password|passwd|secret|api_key|apikey|access_token|auth_token|token|private_key)["']?\s*[:=]\s*["']?)([^"',\s]+)(["']?)"""
        ),
        r"\1[REDACTED]\3",
    ),
    (
        re.compile(r"(https?://[^/\s:@]+:)[^/\s@]+(@)"),
        r"\1[REDACTED]\2",
    ),
)


_SENSITIVE_KEY_NAMES: tuple[str, ...] = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "auth_token",
    "private_key",
)


def redact_sensitive_text(text: str) -> str:
    """Mask credentials, tokens, passwords, and sensitive headers in strings."""
    if not text:
        return text
    result = text
    for pattern, repl in _SENSITIVE_PATTERNS:
        result = pattern.sub(repl, result)
    return result


class SensitiveDataFilter(logging.Filter):
    """Filter that redacts credentials and secrets from log messages and args."""

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                new_dict: dict[Any, Any] = {}
                for k, v in record.args.items():
                    if isinstance(k, str) and any(
                        sk in k.lower() for sk in _SENSITIVE_KEY_NAMES
                    ):
                        new_dict[k] = "[REDACTED]"
                    elif isinstance(v, str):
                        new_dict[k] = redact_sensitive_text(v)
                    else:
                        new_dict[k] = v
                record.args = new_dict
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_sensitive_text(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True


class DuplicateLogFilter(logging.Filter):
    """Sliding-window filter to suppress repeated identical log messages."""

    def __init__(
        self,
        allowed_repetitions: int = 10,
        expire_seconds: float = 300.0,
        max_cache_size: int = 1000,
    ) -> None:
        super().__init__()
        self._allowed_repetitions = max(1, allowed_repetitions)
        self._expire_seconds = max(1.0, expire_seconds)
        self._max_cache_size = max(1, max_cache_size)
        self._lock = threading.RLock()
        self._cache: dict[str, tuple[float, int]] = {}

    def _prune(self, now: float) -> None:
        cutoff = now - self._expire_seconds
        expired = [k for k, (ts, _) in self._cache.items() if ts < cutoff]
        for k in expired:
            del self._cache[k]
        if len(self._cache) >= self._max_cache_size:
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][0])
            for k in sorted_keys[: max(1, len(sorted_keys) // 2)]:
                self._cache.pop(k, None)

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage() if record.msg else ""
        if not msg:
            return True
        key = msg[:100]
        now = time.time()
        with self._lock:
            self._prune(now)
            entry = self._cache.get(key)
            if entry is None or (now - entry[0]) > self._expire_seconds:
                self._cache[key] = (now, 1)
                return True
            first_ts, count = entry
            new_count = count + 1
            self._cache[key] = (first_ts, new_count)
            return new_count <= self._allowed_repetitions


class _ConsoleFormatter(logging.Formatter):
    """Color the level and message while leaving source information readable."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        record = copy.copy(record)
        color = {
            logging.DEBUG: "\x1b[36m",
            logging.INFO: "\x1b[32m",
            logging.WARNING: "\x1b[33m",
            logging.ERROR: "\x1b[31m",
            logging.CRITICAL: "\x1b[35m",
        }.get(record.levelno, "\x1b[37m")
        record.levelname = f"{color}{record.levelname}\x1b[0m"
        record.msg = f"{color}{record.getMessage()}\x1b[0m"
        record.args = None
        return super().format(record)


class _QueueHandler(logging.handlers.QueueHandler):
    """Defer message interpolation and traceback formatting to the worker."""

    @override
    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        return copy.copy(record)


class SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Rotate to unique archives and tolerate transient Windows sharing locks.

    Exhausted lock retries leave the current file in place; the record is still
    written and rotation is attempted again on the next record. Retention is
    checked at startup and on rotation, using archive modification times.
    """

    def __init__(self, filename: Path) -> None:
        filename.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, maxBytes=_MAX_BYTES, encoding="utf-8")
        self._prune_archives()

    def _prune_archives(self) -> None:
        path = Path(self.baseFilename)
        cutoff = time.time() - _RETENTION_SECONDS
        for archive in path.parent.glob(f"{path.name}.*.log"):
            try:
                if archive.stat().st_mtime < cutoff:
                    archive.unlink()
            except OSError:
                # Locked archives are retried during the next retention sweep.
                continue

    @override
    def doRollover(self) -> None:
        if self.stream is not None:
            self.stream.close()
            self.stream = None
        path = Path(self.baseFilename)
        archive = path.with_name(f"{path.name}.{time.time_ns()}.{uuid.uuid4().hex}.log")
        try:
            for attempt in range(_RETRY_ATTEMPTS):
                try:
                    path.rename(archive)
                    break
                except PermissionError:
                    if attempt < _RETRY_ATTEMPTS - 1:
                        time.sleep(0.05 * 2**attempt)
                except FileNotFoundError:
                    break
        finally:
            self.stream = self._open()
        self._prune_archives()


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a standard logger, initializing default logging once on first use.

    Explicit setup_logging() settings are preserved by subsequent calls. Setup is
    serialized so concurrent module imports do not install duplicate handlers.
    """
    with _LOCK:
        if _listener is None:
            setup_logging()
        return logging.getLogger(name)


def setup_logging(
    level: int | str = logging.INFO,
    *,
    log_path: str | Path | None = None,
    console: TextIO | None = None,
    color: bool | None = None,
    filter_duplicates: bool = True,
    redact_secrets: bool = True,
) -> None:
    """Install queued root logging, replacing any previous setup from this module.

    Existing external handlers are preserved. Colors default to terminal detection.
    The unbounded in-process queue avoids waiting for file or console I/O; callers
    should not mutate message arguments after enqueueing. Default paths are rooted
    at the repository, independent of the current working directory.
    """
    global _listener, _queue_handler, _previous_level  # noqa: PLW0603
    with _LOCK:
        shutdown_logging()
        root = logging.getLogger()
        resolved_level = (
            logging.getLevelNamesMapping()[level.upper()]
            if isinstance(level, str)
            else level
        )
        path = (
            Path(log_path)
            if log_path is not None
            else Path(__file__).resolve().parents[3] / "data" / "logs" / "app.log"
        )
        file_handler = SafeRotatingFileHandler(path)
        file_handler.setFormatter(logging.Formatter(_FORMAT, _DATE_FORMAT))
        stream = console if console is not None else sys.stderr
        console_handler = logging.StreamHandler(stream)
        use_color = stream.isatty() if color is None else color
        formatter = _ConsoleFormatter if use_color else logging.Formatter
        console_handler.setFormatter(formatter(_FORMAT, _DATE_FORMAT))
        records: queue.Queue[logging.LogRecord] = queue.Queue()
        handler = _QueueHandler(records)
        if redact_secrets:
            handler.addFilter(SensitiveDataFilter())
        if filter_duplicates:
            handler.addFilter(DuplicateLogFilter())

        listener = logging.handlers.QueueListener(
            records, console_handler, file_handler, respect_handler_level=True
        )
        listener.start()
        _previous_level = root.level
        root.setLevel(resolved_level)
        root.addHandler(handler)
        _queue_handler = handler
        _listener = listener


def shutdown_logging() -> None:
    """Detach the queue, drain pending records, and close owned handlers."""
    global _listener, _queue_handler  # noqa: PLW0603
    with _LOCK:
        if _listener is None:
            return
        root = logging.getLogger()
        if _queue_handler is not None:
            root.removeHandler(_queue_handler)
            _queue_handler.close()
        _listener.stop()
        for handler in _listener.handlers:
            handler.close()
        root.setLevel(_previous_level)
        _listener = None
        _queue_handler = None


def _resolve_debug_setting(settings: Any) -> bool:
    """Extract debug_level_active safely from settings."""
    try:
        scope = getattr(settings, "config_troubleshooting", None)
        if scope is not None:
            val = getattr(scope, "debug_level_active", None)
            if val is not None:
                return bool(val)
        if hasattr(settings, "get_bool"):
            return bool(
                settings.get_bool("config_troubleshooting", "debug_level_active", False)
            )
        if hasattr(settings, "get"):
            return bool(
                settings.get("config_troubleshooting", "debug_level_active", False)
            )
    except Exception:  # noqa: BLE001
        return False
    return False


def activate_debug_logging(
    enabled: bool = True,
    *,
    settings: Any = None,
) -> bool:
    """Set root logging level to DEBUG when active, or restore standard level.

    When settings is provided, resolves debug_level_active from
    settings.config_troubleshooting.debug_level_active.
    """
    if settings is not None:
        enabled = _resolve_debug_setting(settings)

    log = get_logger(__name__)
    root = logging.getLogger()
    if enabled:
        root.setLevel(logging.DEBUG)
        log.info("Activated debug logging level.")
    else:
        root.setLevel(logging.INFO)
        for name in _NOISY_LOGGERS:
            logging.getLogger(name).setLevel(logging.WARNING)
    return enabled


def configure_logging_from_settings(settings: Any) -> bool:
    """Configure logging levels using application settings."""
    active = _resolve_debug_setting(settings)
    activate_debug_logging(enabled=active)
    return active


def emit_startup_diagnostics(
    app_version: str = "1.0.0",
    root_path: Path | str | None = None,
    settings: Any = None,
) -> dict[str, Any]:
    """Emit startup diagnostic telemetry matching donor SQApp.initApp()."""
    log = get_logger(__name__)
    if settings is not None:
        configure_logging_from_settings(settings)

    base = (
        Path(root_path)
        if root_path is not None
        else Path(__file__).resolve().parents[3]
    )

    log.info("Application version: %s", app_version)

    computer_name = (
        os.getenv("COMPUTERNAME") or os.getenv("HOSTNAME") or platform.node()
    )
    user_name = os.getenv("USERNAME") or os.getenv("USER") or "unknown"
    tz = time.tzname[0] if time.tzname else "UTC"
    log.debug(
        "Computer name: %s, User name: %s, Timezone: %s",
        computer_name,
        user_name,
        tz,
    )

    log.debug(
        "Python runtime: %s %s (%s)",
        platform.python_implementation(),
        platform.python_version(),
        platform.platform(),
    )

    hw_info: dict[str, Any] = {"logical_cores": os.cpu_count() or 1}
    try:
        from app.core.host.resources import probe_hardware

        probe = probe_hardware()
        phys = probe.cpu_count_physical or probe.cpu_count_logical
        hw_info["logical_cores"] = probe.cpu_count_logical
        hw_info["physical_cores"] = phys
        hw_info["total_ram_bytes"] = probe.ram_total_bytes
        hw_info["ram_used_pct"] = probe.ram_used_pct
        log.info(
            "HW: cores=%d (phys=%d), ram=%.1f GB (%.1f%% used)",
            probe.cpu_count_logical,
            phys,
            probe.ram_total_bytes / (1024**3),
            probe.ram_used_pct,
        )
    except Exception as exc:  # noqa: BLE001
        log.debug("HW probe fallback: cores=%d (%s)", hw_info["logical_cores"], exc)

    dirs_to_check = [base, base / "data", base / "data" / "logs"]
    writable_map: dict[str, bool] = {}
    for d in dirs_to_check:
        try:
            d.mkdir(parents=True, exist_ok=True)
            test_file = d / f".probe_write_{uuid.uuid4().hex}.tmp"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink()
            writable_map[str(d)] = True
        except OSError:
            writable_map[str(d)] = False
            log.warning("Storage directory not writable: %s", d)

    diagnostics: dict[str, Any] = {
        "app_version": app_version,
        "computer_name": computer_name,
        "user_name": user_name,
        "timezone": tz,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "hardware": hw_info,
        "writable_directories": writable_map,
    }
    log.debug("Startup diagnostics completed successfully.")
    return diagnostics


class CLILogger:
    """Thread-safe task and CLI output logger with optional file redirection."""

    _instance: CLILogger | None = None
    _lock: threading.RLock = threading.RLock()

    def __init__(self) -> None:
        self._file: TextIO | None = None
        self._path: Path | None = None
        self._file_lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> CLILogger:
        """Return singleton CLILogger instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def redirect_output_to_file(self, target: Path | str | None) -> None:
        """Redirect task output to target path or close when target is None."""
        with self._file_lock:
            self.close_file()
            if target is None:
                return
            p = Path(target)
            p.parent.mkdir(parents=True, exist_ok=True)
            self._file = p.open("a", encoding="utf-8")
            self._path = p

    def close_file(self) -> None:
        """Flush and close active redirected file stream if opened."""
        with self._file_lock:
            if self._file is not None:
                try:
                    self._file.flush()
                    self._file.close()
                except OSError:
                    pass
                self._file = None
                self._path = None

    def log(self, message: str, *, add_separator: bool = False) -> None:
        """Log structured message to file stream or standard host logger."""
        if not message.strip() or message == "{}":
            return
        formatted = message.replace("<br>", "\n")
        if add_separator:
            formatted = f"{formatted}\n{_CLI_SEPARATOR}"
        with self._file_lock:
            if self._file is not None:
                self._file.write(formatted + "\n")
                self._file.flush()
            else:
                get_logger(__name__).info("%s", formatted)


def redirect_cli_output(path: Path | str | None) -> None:
    """Redirect CLI output to the specified file path, or close redirection if None."""
    CLILogger.get_instance().redirect_output_to_file(path)


atexit.register(shutdown_logging)


if __name__ == "__main__":
    setup_logging(level=logging.INFO)
    logger = get_logger(__name__)
    emit_startup_diagnostics(app_version="1.0.0")
    logger.debug("This is a debug message")
    logger.info("This is an info message with secret token=secret12345")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
