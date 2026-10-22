"""Redacted formatting for console and file telemetry."""

from __future__ import annotations

import copy
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import override

from .security import normalize_path, redact_mapping, redact_value

ERROR_BOUNDARY_FR = "FR-HOST-LOGGING-ERROR-BOUNDARY"
FORMATTING_FR = "FR-HOST-LOGGING-FORMATTING"
ANSI_RESET: str = "\033[0m"
ANSI_LEVEL_COLORS: dict[str, str] = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[1;35m",  # Bold Magenta
}

class LogEventFormatter(logging.Formatter):
    """Structured formatter with timestamp, ANSI styling, and safe error boundary."""

    def __init__(
        self,
        *,
        colorize: bool = False,
        root_dir: Path | None = None,
    ) -> None:
        """Initialize formatter with optional colorization and path normalization.

        Args:
            colorize: True to apply ANSI color codes to level and message.
            root_dir: Optional root path for machine path normalization.
        """
        super().__init__()
        self.colorize = colorize
        self.root_dir = root_dir

    @override
    def format(self, record: logging.LogRecord) -> str:
        """Format: YYYY-MM-DD HH:MM:SS.mmm | LEVEL | module:function:line - message.

        Args:
            record: Logging log record instance to format.

        Returns:
            Formatted log event string.
        """
        # Never cache unsanitized exception text on another handler's record.
        record = copy.copy(record)
        original_msg = record.msg
        original_args = record.args

        try:
            record_dt = datetime.fromtimestamp(record.created, tz=UTC)
            time_str = (
                record_dt.strftime("%Y-%m-%d %H:%M:%S") + f".{int(record.msecs):03d}"
            )

            if isinstance(record.args, dict):
                record.args = redact_mapping(record.args, fingerprint=True)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_value(arg, fingerprint=True)
                    if not isinstance(arg, str)
                    else arg
                    for arg in record.args
                )

            try:
                raw_msg = record.getMessage()
            except Exception:  # noqa: BLE001
                raw_msg = (
                    f"[LOGGING-ERROR-BOUNDARY] Failed to format message "
                    f"| Raw: {record.msg}"
                )

            clean_msg = normalize_path(
                str(redact_value(raw_msg, fingerprint=True)), self.root_dir
            )

            caller = f"{record.name}:{record.funcName}:{record.lineno}"

            level_name = record.levelname
            if self.colorize:
                color = ANSI_LEVEL_COLORS.get(level_name, "")
                formatted_level = f"{color}{level_name:<5}{ANSI_RESET}"
                formatted_msg = f"{color}{clean_msg}{ANSI_RESET}"
            else:
                formatted_level = f"{level_name:<5}"
                formatted_msg = clean_msg

            formatted = f"{time_str} | {formatted_level} | {caller} - {formatted_msg}"

            if record.exc_info and not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            if record.exc_text:
                scrubbed_exc = normalize_path(
                    str(redact_value(record.exc_text, fingerprint=True)),
                    self.root_dir,
                )
                formatted = f"{formatted}\n{scrubbed_exc}"

            if record.stack_info:
                scrubbed_stack = normalize_path(
                    str(
                        redact_value(
                            self.formatStack(record.stack_info), fingerprint=True
                        )
                    ),
                    self.root_dir,
                )
                formatted = f"{formatted}\n{scrubbed_stack}"

            return formatted

        except Exception:  # noqa: BLE001
            return "[LOGGING-ERROR-BOUNDARY] Unable to format telemetry record"
        finally:
            record.msg = original_msg
            record.args = original_args


