"""Unit tests for application composition root and CLI entry point."""

import asyncio
import json

import pytest
from app.main import async_main, parse_args
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
        ]
    )
    assert args.profile == "default"
    assert args.enabled == ["feat1", "feat2"]
    assert args.log_level == "DEBUG"
    assert args.dry_run is True
    assert args.status is True
    assert args.list_profiles is True


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
