"""Unit tests for application composition root and CLI entry point."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.main import (
    _run_ui_server,
    _terminate_process_tree,
    async_main,
    parse_args,
    run,
)
from app.registry import available_profiles


def test_parse_args_defaults() -> None:
    """Verify default CLI arguments."""
    args = parse_args([])
    assert args.profile is None
    assert args.enabled is None
    assert args.log_level == "INFO"
    assert args.dry_run is False
    assert args.status is False
    assert args.list_profiles is False
    assert args.ui is False


def test_parse_args_custom_values() -> None:
    """Verify custom CLI argument parsing."""
    args = parse_args(
        [
            "--profile",
            "default",
            "--enabled",
            "feat1",
            "feat2",
            "--log-level",
            "debug",
            "--dry-run",
            "--status",
            "--list-profiles",
            "--ui",
        ]
    )
    assert args.profile == "default"
    assert args.enabled == ["feat1", "feat2"]
    assert args.log_level == "DEBUG"
    assert args.dry_run is True
    assert args.status is True
    assert args.list_profiles is True
    assert args.ui is True


def test_list_profiles_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify --list-profiles outputs valid JSON profile list."""
    exit_code = asyncio.run(async_main(["--list-profiles"]))
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "default" in data


def test_status_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify --status outputs valid JSON status payload."""
    exit_code = asyncio.run(async_main(["--status"]))
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "ready"
    assert "active_features" in data


def test_dry_run_flag() -> None:
    """Verify --dry-run boots runtime and exits cleanly."""
    exit_code = asyncio.run(async_main(["--dry-run"]))
    assert exit_code == 0


def test_dry_run_with_ui() -> None:
    """Verify --dry-run with --ui validates ui directory and exits cleanly."""
    exit_code = asyncio.run(async_main(["--dry-run", "--ui"]))
    assert exit_code == 0


def test_dry_run_with_ui_invalid_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify --dry-run with missing ui package.json returns error code 1."""
    from app import main

    monkeypatch.setattr(main, "UI_DIR", tmp_path)
    exit_code = asyncio.run(async_main(["--dry-run", "--ui"]))
    assert exit_code == 1


def test_invalid_profile_returns_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify invalid profile returns exit code 1 with error message."""
    exit_code = asyncio.run(async_main(["--profile", "invalid_profile"]))
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Configuration error" in captured.err


def test_available_profiles_helper() -> None:
    """Verify available_profiles helper returns sorted profile names."""
    profiles = available_profiles()
    assert "default" in profiles
    assert list(profiles) == sorted(profiles)


def test_terminate_process_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify _terminate_process_tree invokes taskkill on Windows and handles errors."""
    mock_run = MagicMock()
    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(sys, "platform", "win32")

    _terminate_process_tree(12345)
    assert mock_run.called
    assert "taskkill" in mock_run.call_args[0][0][0].lower()

    mock_run.side_effect = OSError("Access denied")
    _terminate_process_tree(12345)


def test_run_ui_server_invalid_directory(tmp_path: Path) -> None:
    """Verify _run_ui_server returns 1 if directory is missing package.json."""
    exit_code = asyncio.run(_run_ui_server(tmp_path))
    assert exit_code == 1


def test_ui_server_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify --ui launches frontend dev server and terminates cleanly."""
    mock_proc = MagicMock()
    mock_proc.pid = 99999
    mock_proc.returncode = None

    async def _mock_wait() -> int:
        mock_proc.returncode = 0
        return 0

    mock_proc.wait = AsyncMock(side_effect=_mock_wait)
    mock_proc.terminate = MagicMock()
    mock_proc.kill = MagicMock()

    mock_create_proc = AsyncMock(return_value=mock_proc)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_create_proc)

    async def _test() -> int:
        stop_event = asyncio.Event()
        stop_event.set()
        return await async_main(["--ui"], stop_event=stop_event)

    exit_code = asyncio.run(_test())
    assert exit_code == 0
    assert mock_create_proc.called
    assert "run" in mock_create_proc.call_args[0]
    assert "dev" in mock_create_proc.call_args[0]


def test_ui_server_cleanup_active_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify _run_ui_server terminates active process if stop_event fires."""
    mock_proc = MagicMock()
    mock_proc.pid = 99999
    mock_proc.returncode = None

    wait_calls = 0

    async def _mock_wait() -> int:
        nonlocal wait_calls
        wait_calls += 1
        if wait_calls == 1:
            await asyncio.Event().wait()
        mock_proc.returncode = 0
        return 0

    mock_proc.wait = AsyncMock(side_effect=_mock_wait)
    mock_proc.terminate = MagicMock()
    mock_proc.kill = MagicMock()

    mock_create_proc = AsyncMock(return_value=mock_proc)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_create_proc)

    stop_event = asyncio.Event()
    stop_event.set()

    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    exit_code = asyncio.run(
        _run_ui_server(ui_dir, stop_event=stop_event, wait_timeout=1.0)
    )
    assert exit_code == 0
    assert mock_create_proc.called


def test_ui_server_cleanup_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify _run_ui_server kills process if terminate times out."""
    mock_proc = MagicMock()
    mock_proc.pid = 99999
    mock_proc.returncode = None

    killed = False

    def _mock_kill() -> None:
        nonlocal killed
        killed = True

    mock_proc.kill = MagicMock(side_effect=_mock_kill)
    mock_proc.terminate = MagicMock()

    async def _mock_wait() -> int:
        if killed:
            mock_proc.returncode = 0
            return 0
        await asyncio.Event().wait()
        return 0

    mock_proc.wait = AsyncMock(side_effect=_mock_wait)

    mock_create_proc = AsyncMock(return_value=mock_proc)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_create_proc)

    stop_event = asyncio.Event()
    stop_event.set()

    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    exit_code = asyncio.run(
        _run_ui_server(ui_dir, stop_event=stop_event, wait_timeout=0.01)
    )
    assert exit_code == 0
    assert mock_proc.kill.called


def test_ui_server_spawn_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify --ui handles subprocess creation failure gracefully."""
    mock_create_proc = AsyncMock(side_effect=OSError("Command not found"))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", mock_create_proc)

    exit_code = asyncio.run(async_main(["--ui"]))
    assert exit_code == 1


def test_ui_server_npm_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify --ui handles missing npm executable gracefully."""
    import shutil

    monkeypatch.setattr(shutil, "which", lambda *args, **kwargs: None)
    exit_code = asyncio.run(async_main(["--ui"]))
    assert exit_code == 1


def test_run_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify synchronous run() entrypoint handles sys.exit and KeyboardInterrupt."""
    with pytest.raises(SystemExit) as excinfo:
        run(["--status"])
    assert excinfo.value.code == 0

    def _mock_run_keyboard_interrupt(coro: Any) -> int:
        coro.close()
        raise KeyboardInterrupt

    monkeypatch.setattr(asyncio, "run", _mock_run_keyboard_interrupt)
    with pytest.raises(SystemExit) as excinfo:
        run(["--dry-run"])
    assert excinfo.value.code == 0
