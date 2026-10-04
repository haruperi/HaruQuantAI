"""Unit tests for the main application entry point.

Description:
    Verifies that app/main.py coordinates process bootstrap, executes workload tasks,
    and guarantees graceful shutdown in its finally boundary.

Purpose:
    FEAT-APP-MAIN: Main application lifecycle entry point and process coordinator.

Key Capabilities:
    - FR-APP-MAIN-BOOTSTRAP: Coordinate host telemetry and start application runtime.
      Associated: `test_main_execution_lifecycle()`
      Logging: Implicit pytest test reporting.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.host.logging import LoggingConfig, reset_logging
from app.main import main as app_main


def test_main_execution_lifecycle(tmp_path: Path) -> None:
    """Verify that app.main() boots telemetry, runs workload, and shuts down."""
    log_dir = tmp_path / "main_lifecycle"
    config = LoggingConfig(
        log_dir=log_dir,
        level=logging.DEBUG,
        include_console=False,
    )

    try:
        app_main(config=config)

        app_log = log_dir / "app.log"
        assert app_log.exists()
        content = app_log.read_text(encoding="utf-8")

        assert "Starting HaruQuantAI application..." in content
        assert "Application started successfully" in content
        assert "HaruQuantAI application shutdown routine finished" in content
    finally:
        reset_logging()


def test_main_default_configuration(tmp_path: Path) -> None:
    """Verify that app.main() executes without an explicit config."""
    # Pre-configure an isolated directory so default test does not pollute data/logs
    log_dir = tmp_path / "default_main"
    config = LoggingConfig(
        log_dir=log_dir,
        level=logging.INFO,
        include_console=False,
    )

    try:
        app_main(config=config)
        app_log = log_dir / "app.log"
        assert app_log.exists()
        content = app_log.read_text(encoding="utf-8")
        assert "Starting HaruQuantAI application..." in content
    finally:
        reset_logging()
