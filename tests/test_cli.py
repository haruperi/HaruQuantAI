"""Unit tests for the CLI entry point module.

Description:
    Verifies that app/cli.py resolves its logger safely at import, emits all five
    severities when main() is executed, queries host settings via show_settings(),
    and flushes output cleanly to disk.

Purpose:
    FEAT-APP-CLI: Command-line interface and diagnostic test dispatch.

Key Capabilities:
    - FR-APP-CLI-DISPATCH: Emit multi-severity diagnostic records and flush telemetry.
      Associated: `test_cli_main_emits_expected_severities()`,
      `test_cli_main_default_settings_fallback()`
      Logging: Implicit pytest test reporting.
    - FR-APP-CLI-SETTINGS: Query and display host database settings via telemetry.
      Associated: `test_show_settings_seeded()`,
      `test_show_settings_missing_database()`, `test_show_settings_empty_database()`
      Logging: Implicit pytest test reporting.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from app.cli import main as cli_main
from app.cli import show_settings
from app.host.logging import configure_host_logging, flush, reset_logging
from app.host.persistance import SettingsStore
from app.host.settings import HostSettings


def test_cli_main_emits_expected_severities(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that cli main() emits events across all log levels and flushes to disk."""
    log_dir = tmp_path / "cli_logs"
    db_file = tmp_path / "isolated.db"
    store = SettingsStore(db_file)
    store.initialize()
    host_settings = HostSettings(db_path=db_file)
    monkeypatch.setattr("app.cli.settings", host_settings)

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


def test_show_settings_seeded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify show_settings reads seeded records and logs each entry."""
    log_dir = tmp_path / "seeded_logs"
    db_file = tmp_path / "seeded.db"
    store = SettingsStore(db_file)
    store.initialize()
    store.update_settings(
        scope="application",
        values={"theme": "dark", "timeout": 30},
    )
    host_settings = HostSettings(db_path=db_file)
    monkeypatch.setattr("app.cli.settings", host_settings)

    configure_host_logging(log_dir=log_dir, level=logging.DEBUG, include_console=False)
    try:
        displayed = show_settings(limit=10)
        assert len(displayed) == 2
        assert displayed["theme"] == "dark"
        assert displayed["timeout"] == 30

        flush(timeout=5.0)

        app_log = log_dir / "app.log"
        assert app_log.exists()
        app_text = app_log.read_text(encoding="utf-8")
        assert "Loaded setting theme = dark" in app_text
        assert "Loaded setting timeout = 30" in app_text
    finally:
        reset_logging()


def test_show_settings_missing_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify show_settings handles non-existent database file gracefully."""
    log_dir = tmp_path / "missing_db_logs"
    db_file = tmp_path / "does_not_exist.db"
    host_settings = HostSettings(db_path=db_file)
    monkeypatch.setattr("app.cli.settings", host_settings)

    configure_host_logging(log_dir=log_dir, level=logging.DEBUG, include_console=False)
    try:
        displayed = show_settings()
        assert displayed == {}

        flush(timeout=5.0)

        app_log = log_dir / "app.log"
        assert app_log.exists()
        app_text = app_log.read_text(encoding="utf-8")
        assert "No settings loaded from host database" in app_text
    finally:
        reset_logging()


def test_show_settings_empty_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify show_settings handles empty database gracefully."""
    log_dir = tmp_path / "empty_logs"
    db_file = tmp_path / "empty.db"
    store = SettingsStore(db_file)
    store.initialize()
    host_settings = HostSettings(db_path=db_file)
    monkeypatch.setattr("app.cli.settings", host_settings)

    configure_host_logging(log_dir=log_dir, level=logging.DEBUG, include_console=False)
    try:
        displayed = show_settings()
        assert displayed == {}

        flush(timeout=5.0)

        app_log = log_dir / "app.log"
        assert app_log.exists()
        app_text = app_log.read_text(encoding="utf-8")
        assert "No settings loaded from host database" in app_text
    finally:
        reset_logging()


def test_cli_main_default_settings_fallback(tmp_path: Path) -> None:
    """Verify cli main() works with default settings parameter without error."""
    log_dir = tmp_path / "default_logs"
    configure_host_logging(log_dir=log_dir, level=logging.DEBUG, include_console=False)
    try:
        cli_main()
        app_log = log_dir / "app.log"
        assert app_log.exists()
        app_text = app_log.read_text(encoding="utf-8")
        assert "This is a info" in app_text
    finally:
        reset_logging()
