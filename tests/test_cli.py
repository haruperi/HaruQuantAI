"""Unit tests for the CLI entry point module.

Description:
    Verifies that app/cli.py resolves its logger safely at import, emits all five
    severities when main() is executed, and flushes output cleanly to disk.

Purpose:
    FEAT-APP-CLI: Command-line interface and diagnostic test dispatch.

Key Capabilities:
    - FR-APP-CLI-DISPATCH: Emit multi-severity diagnostic records and flush telemetry.
      Associated: `test_cli_main_emits_expected_severities()`
      Logging: Implicit pytest test reporting.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.cli import main as cli_main
from app.host.logging import configure_host_logging, reset_logging


def test_cli_main_emits_expected_severities(tmp_path: Path) -> None:
    """Verify that cli main() emits events across all log levels and flushes to disk."""
    log_dir = tmp_path / "cli_logs"
    configure_host_logging(log_dir=log_dir, level=logging.DEBUG, include_console=False)

    try:
        cli_main()

        app_log = log_dir / "app.log"
        debug_log = log_dir / "debug.log"
        errors_log = log_dir / "errors.log"

        assert app_log.exists()
        assert debug_log.exists()
        assert errors_log.exists()

        app_text = app_log.read_text(encoding="utf-8")
        assert "This is a debug" in app_text
        assert "This is a info" in app_text
        assert "This is a warning" in app_text
        assert "This is a error" in app_text
        assert "This is a critical" in app_text

        debug_text = debug_log.read_text(encoding="utf-8")
        assert "This is a debug" in debug_text

        errors_text = errors_log.read_text(encoding="utf-8")
        assert "This is a error" in errors_text
        assert "This is a critical" in errors_text
    finally:
        reset_logging()
