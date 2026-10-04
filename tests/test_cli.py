"""Unit tests for the CLI entry point module.

Description:
    Verifies that app/cli.py coordinates process bootstrap, executes initial
    runtime sanity checks, validates workspace paths, dynamically resolves debug
    telemetry log level based on troubleshooting configuration, and guarantees
    graceful shutdown in a finally boundary.

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


def _seed_basic_cli_settings(
    store: SettingsStore, root_dir: Path | None = None
) -> None:
    """Seed baseline user, hardware, and workspace path settings."""
    store.update_settings(
        "user_access",
        {"username": "test_user", "locked": False, "session_timeout_mins": 60},
    )
    store.update_settings("config_cpu", {"custom_cores": 4})
    store.update_settings("config_memory", {"memory_limit_gb": 8})
    store.update_settings("config_troubleshooting", {"debug_level_active": False})

    if root_dir is not None:
        configs = root_dir / "presets"
        configs.mkdir(parents=True, exist_ok=True)
        data = root_dir / "market"
        data.mkdir(parents=True, exist_ok=True)
        projects = root_dir / "projects"
        projects.mkdir(parents=True, exist_ok=True)
        strategies = root_dir / "strategies"
        strategies.mkdir(parents=True, exist_ok=True)
        store.update_settings(
            "workspace_paths",
            {
                "configs_dir": str(configs),
                "data_dir": str(data),
                "projects_dir": str(projects),
                "strategies_dir": str(strategies),
            },
        )
    else:
        store.update_settings(
            "workspace_paths",
            {
                "configs_dir": "data/presets",
                "data_dir": "data/market",
                "projects_dir": "data/projects",
                "strategies_dir": "data/strategies",
            },
        )


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
    _seed_basic_cli_settings(store, root_dir=tmp_path)
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
    _seed_basic_cli_settings(store, root_dir=tmp_path)
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


def test_cli_main_aborts_when_workspace_path_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that cli main() logs error and exits early if a workspace path is missing."""
    db_file = tmp_path / "missing_path.db"
    store = SettingsStore(db_file)
    store.initialize()
    _seed_basic_cli_settings(store, root_dir=tmp_path)
    store.update_settings(
        "workspace_paths",
        {
            "configs_dir": str(tmp_path / "does_not_exist_presets"),
            "data_dir": "data/market",
            "projects_dir": "data/projects",
            "strategies_dir": "data/strategies",
        },
    )
    host_settings = HostSettings(db_path=db_file)
    monkeypatch.setattr("app.cli.settings", host_settings)

    captured_logs: list[str] = []

    def mock_error(msg: str, *args: Any, **kwargs: Any) -> None:
        captured_logs.append(msg % args if args else msg)

    monkeypatch.setattr("app.host.settings.logger.error", mock_error)

    cli_main()
    assert any("Configs directory does not exist" in msg for msg in captured_logs)


def test_cli_main_aborts_when_user_locked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that cli main() aborts early when user_access.locked is True."""
    db_file = tmp_path / "locked_user.db"
    store = SettingsStore(db_file)
    store.initialize()
    _seed_basic_cli_settings(store, root_dir=tmp_path)
    store.update_settings("user_access", {"locked": True})
    host_settings = HostSettings(db_path=db_file)
    monkeypatch.setattr("app.cli.settings", host_settings)

    captured_logs: list[str] = []

    def mock_error(msg: str, *args: Any, **kwargs: Any) -> None:
        captured_logs.append(msg % args if args else msg)

    monkeypatch.setattr("app.cli.logger.error", mock_error)

    cli_main()
    assert any("Application is locked" in msg for msg in captured_logs)


def test_cli_main_records_session_in_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that cli main() initializes host_session table and records session."""
    db_file = tmp_path / "session_cli.db"
    store = SettingsStore(db_file)
    store.initialize()
    _seed_basic_cli_settings(store, root_dir=tmp_path)
    host_settings = HostSettings(db_path=db_file)
    monkeypatch.setattr("app.cli.settings", host_settings)

    cli_main()

    import sqlite3

    conn = sqlite3.connect(db_file)
    rows = conn.execute(
        "SELECT session_id, username, peer_id, status FROM host_session"
    ).fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0][1] == "test_user"
    assert rows[0][2] == "cli-local"
    assert rows[0][3] == "ACTIVE"


def test_cli_main_initializes_jobs_system(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that cli main() initializes hardware diagnostics and JobManager."""
    db_file = tmp_path / "jobs_cli.db"
    store = SettingsStore(db_file)
    store.initialize()
    _seed_basic_cli_settings(store, root_dir=tmp_path)
    host_settings = HostSettings(db_path=db_file)
    monkeypatch.setattr("app.cli.settings", host_settings)

    closed: list[bool] = []
    from app.host import jobs as host_jobs

    original_close = host_jobs.JobManager.close

    def spy_close(self: Any, *args: Any, **kwargs: Any) -> None:
        closed.append(True)
        original_close(self, *args, **kwargs)

    monkeypatch.setattr("app.host.jobs.JobManager.close", spy_close)

    cli_main()
    assert len(closed) >= 1
