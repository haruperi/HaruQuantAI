"""Command-line verification of the host logging feature."""

from __future__ import annotations

import logging
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .formatting import FORMATTING_FR
from .runtime import (
    BOUND_LOGGER_FR,
    CORRELATION_FR,
    EXPORTS_FR,
    WORKER_FR,
    TelemetryLogger,
    flush_logs,
    get_access_logger,
    get_logger,
    reset_correlation_id,
    set_correlation_id,
    setup_logging,
    shutdown_logging,
)
from .security import REDACTION_FR
from .sinks import SINKS_FR


class TelemetryLoggerCLI:
    """Command-line interface and self-verification runner for TelemetryLogger."""

    @staticmethod
    def format_output(result: Mapping[str, Any]) -> str:
        """Format verification result dictionary for CLI display."""
        return "\n".join(f"{k}: {v}" for k, v in result.items())

    @classmethod
    def run_cli(cls, argv: Sequence[str] | None = None) -> int:
        """Execute telemetry self-verification across all 9 FR capabilities."""
        args = list(argv) if argv is not None else []
        verify_mode = "--verify" in args or not args

        with tempfile.TemporaryDirectory(
            prefix="hqai_logging_cli_", ignore_cleanup_errors=True
        ) as tmp_dir:
            log_dir = Path(tmp_dir) / "logs"
            ws_events: list[dict[str, Any]] = []
            try:
                ring = setup_logging(log_dir, level=logging.DEBUG, async_engine=False)
                TelemetryLogger.register_ws_sink(ws_events.append)
                logger = get_logger("haruquantai.demo")

                logger.info(
                    "1. Telemetry Worker & Engine initialized",
                    extra={"fr_id": WORKER_FR},
                )
                secret_logger = logger.bind(
                    token="super_secret_token_12345",  # noqa: S106
                    password="my_admin_password",  # noqa: S106
                )
                secret_logger.info(
                    "2. Secret & Path Redaction applied (path=%s)",
                    str(Path.cwd() / "data" / "database"),
                    extra={"fr_id": REDACTION_FR},
                )
                logger.warning(
                    "3. Safe Error Boundary & ANSI warning format",
                    extra={"fr_id": FORMATTING_FR},
                )
                logger.error(
                    "4. Error sink verification event",
                    extra={"fr_id": SINKS_FR},
                )
                bound = logger.bind(session_id="sess-8899", symbol="BTC/USDT")
                bound.emit(
                    "INFO", "5. Bound logger emit", extra={"fr_id": BOUND_LOGGER_FR}
                )

                token = set_correlation_id("req-uuid-990011")
                try:
                    logger.info(
                        "6. Correlation ID propagated",
                        extra={"fr_id": CORRELATION_FR},
                    )
                finally:
                    reset_correlation_id(token)

                get_access_logger().info(
                    "7. Access logger routed",
                    extra={"fr_id": EXPORTS_FR},
                )
                flush_logs()

                queried = ring.query(min_level="INFO")
                files_ok = all(
                    (log_dir / name).exists()
                    for name in ("app.log", "access.log", "errors.log")
                )
                summary = {
                    "verified": bool(
                        verify_mode and files_ok and queried and ws_events
                    ),
                    "records_queried": len(queried),
                    "ws_events_received": len(ws_events),
                    "sinks_created": files_ok,
                }
                sys.stdout.write(cls.format_output(summary) + "\n")
                return 0 if summary["verified"] else 1
            finally:
                shutdown_logging()
