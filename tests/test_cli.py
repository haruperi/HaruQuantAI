"""Unit tests for the CLI entry point module.

Description:
    Verifies that app/cli.py coordinates process bootstrap, executes initial
    runtime sanity checks, dynamically resolves debug telemetry log level based on
    troubleshooting configuration, and guarantees graceful shutdown in a finally boundary.

Purpose:
    FEAT-APP-CLI: CLI application lifecycle entry point and process coordinator.

Key Capabilities:
    - FR-APP-CLI-BOOTSTRAP: Coordinate host telemetry and start application runtime.
      Associated: `test_cli_main_execution_lifecycle()`
      Logging: Implicit pytest test reporting.
    - FR-APP-CLI-LIFECYCLE: Coordinate graceful process shutdown and telemetry sync.
      Associated: `test_cli_main_execution_lifecycle()`
      Logging: Implicit pytest test reporting.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from app.cli import main as cli_main
from app.host.logging import reset_logging
from app.host.persistance import SettingsStore
from app.host.settings import HostSettings

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def _isolate_test_logging() -> Generator[None]:
    """Ensure clean telemetry isolation before and after each test."""
    reset_logging()
    yield
    reset_logging()


def _seed_basic_cli_settings(store: SettingsStore) -> None:
    """Seed baseline user and hardware settings required for CLI banner printing."""
    store.update_settings("user_access", {"username": "test_user"})
    store.update_settings("config_cpu", {"custom_cores": 4})
    store.update_settings("config_memory", {"memory_limit_gb": 8})


def test_cli_main_execution_lifecycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that cli main() boots telemetry, logs startup, and shuts down cleanly."""
    log_dir = tmp_path / "cli_lifecycle"
    from app.host import logging as host_logging

    def isolated_configure(*args: Any, **kwargs: Any) -> Any:
        kwargs["log_dir"] = log_dir
        kwargs["include_console"] = False
        return host_logging.configure_host_logging(**kwargs)

    monkeypatch.setattr("app.cli.configure_host_logging", isolated_configure)

    try:
        cli_main()

        app_log = log_dir / "app.log"
        assert app_log.exists()
        content = app_log.read_text(encoding="utf-8")

        assert "Application started successfully" in content
        assert "Application shutdown... Routine finished" in content
    finally:
        reset_logging()


def test_cli_main_debug_level_override_when_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that debug_level_active=True overrides log level to DEBUG."""
    db_file = tmp_path / "active_debug.db"
    store = SettingsStore(db_file)
    store.initialize()
    _seed_basic_cli_settings(store)
    store.update_settings(
        scope="config_troubleshooting",
        values={"debug_level_active": True},
    )
    host_settings = HostSettings(db_path=db_file)
    monkeypatch.setattr("app.cli.settings", host_settings)

    captured_kwargs: dict[str, Any] = {}
    from app.host import logging as host_logging

    def spy_configure(**kwargs: Any) -> Any:
        captured_kwargs.update(kwargs)
        return host_logging.TelemetryEngine.get_or_create()

    monkeypatch.setattr("app.cli.configure_host_logging", spy_configure)

    try:
        cli_main()
        assert captured_kwargs.get("level") == "DEBUG"
    finally:
        reset_logging()


def test_cli_main_uses_info_level_when_inactive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that debug_level_active=False configures INFO level."""
    db_file = tmp_path / "inactive_debug.db"
    store = SettingsStore(db_file)
    store.initialize()
    _seed_basic_cli_settings(store)
    store.update_settings(
        scope="config_troubleshooting",
        values={"debug_level_active": False},
    )
    host_settings = HostSettings(db_path=db_file)
    monkeypatch.setattr("app.cli.settings", host_settings)

    captured_kwargs: dict[str, Any] = {}
    from app.host import logging as host_logging

    def spy_configure(**kwargs: Any) -> Any:
        captured_kwargs.update(kwargs)
        return host_logging.TelemetryEngine.get_or_create()

    monkeypatch.setattr("app.cli.configure_host_logging", spy_configure)

    try:
        cli_main()
        assert captured_kwargs.get("level") == "INFO"
    finally:
        reset_logging()
