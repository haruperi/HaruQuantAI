"""Dated file logging for the host process.

Logs live under ``data/logs`` by default, one file per calendar day (UTC),
matching the SQX shell's dated-log convention (ledger SQX144-EV-000001).
Messages must never contain secrets, credentials, or personal data — access
lines record method, path, status, and request id, never payloads.
"""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

LOGGER_NAME = "haruquantai.host"
_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def host_log_path(log_dir: Path, day: datetime | None = None) -> Path:
    """Return the dated log file path directly under ``log_dir``.

    Args:
        log_dir: Directory that will hold the log files (created separately
            by :func:`configure_host_logging`).
        day: Override the date used in the filename (tests); defaults to the
            current UTC date.

    Returns:
        A path of the form ``<log_dir>/log_<Y>_<M>_<D>.log``.
    """
    resolved_day = day if day is not None else datetime.now(tz=UTC)
    return (
        log_dir
        / f"log_{resolved_day.year}_{resolved_day.month:02d}_{resolved_day.day:02d}.log"
    )


def configure_host_logging(
    log_dir: Path, *, also_stderr: bool = True
) -> logging.Logger:
    """Configure and return the host logger writing dated files under ``log_dir``.

    The call is idempotent: an already-configured logger is returned
    unchanged, so repeated invocations (tests, re-entry) never duplicate
    handlers or reopen files. The logger does not propagate to the root
    logger, keeping host output out of test-capture noise.

    Args:
        log_dir: Target directory; created (with parents) when missing.
        also_stderr: Also mirror records to stderr for live terminal use;
            tests disable this to keep output clean.

    Returns:
        The ``haruquantai.host`` logger with at least one file handler.
    """
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(host_log_path(log_dir), encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    logger.addHandler(file_handler)

    if also_stderr:
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(stream_handler)

    return logger
