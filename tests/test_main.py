"""Tests for main application entry point and composition bootstrap CLI."""

import json
import logging
from pathlib import Path
from typing import override

import pytest

from app.composition.logging import (
    _OWNED_HANDLER_ATTR,
    CleanupDiagnostic,
    LoggingConfig,
    compute_secret_fingerprint,
    configure_logging,
)
from app.main import async_main, run


@pytest.mark.asyncio
async def test_main_default_invocation(capsys: pytest.CaptureFixture[str]) -> None:
    """Test default CLI invocation without arguments prints greeting and exits cleanly."""
    exit_code = await async_main([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "HaruQuantAI initialized" in captured.out


@pytest.mark.asyncio
async def test_main_status_without_config(capsys: pytest.CaptureFixture[str]) -> None:
    """Test --status prints valid JSON diagnostics."""
    exit_code = await async_main(["--status"])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "profile" in data
    assert "is_ready" in data
    assert "capabilities" in data


@pytest.mark.asyncio
async def test_main_status_with_example_configs(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test --status with research, backtest, and live example configurations."""
    # Research config
    code_research = await async_main(
        ["--config", "config/examples/research.toml", "--status"]
    )
    assert code_research == 0
    res_data = json.loads(capsys.readouterr().out)
    assert res_data["profile"] == "research"

    # Backtest config
    code_backtest = await async_main(
        ["--config", "config/examples/backtest.toml", "--status"]
    )
    assert code_backtest == 0
    bt_data = json.loads(capsys.readouterr().out)
    assert bt_data["profile"] == "backtest"

    # Live config (profile is live, missing capabilities expected, but exits 0)
    code_live = await async_main(["--config", "config/examples/live.toml", "--status"])
    assert code_live == 0
    live_data = json.loads(capsys.readouterr().out)
    assert live_data["profile"] == "live"
    assert live_data["is_ready"] is False
    assert len(live_data["missing_profile_capabilities"]) > 0


@pytest.mark.asyncio
async def test_main_invalid_config_file(capsys: pytest.CaptureFixture[str]) -> None:
    """Test providing a non-existent configuration file returns non-zero exit code."""
    exit_code = await async_main(["--config", "nonexistent_file.toml"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "[ERROR]" in captured.out


def test_main_run_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test synchronous run() entry point calls sys.exit."""
    monkeypatch.setattr("sys.argv", ["haruquantai", "--status"])
    with pytest.raises(SystemExit) as exc_info:
        run()
    assert exc_info.value.code == 0


@pytest.mark.asyncio
async def test_main_logging_options_and_file_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Launcher supports --log-level and --log-file while preserving stdout status JSON."""
    log_file = tmp_path / "launcher.log"

    exit_code = await async_main(
        [
            "--log-level",
            "DEBUG",
            "--log-file",
            str(log_file),
            "--status",
        ]
    )
    assert exit_code == 0

    # stdout must remain valid JSON
    captured = capsys.readouterr()
    status_data = json.loads(captured.out)
    assert "profile" in status_data

    # Log file must exist and contain structured records
    assert log_file.is_file()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 2
    records = [json.loads(line) for line in lines]
    events = [r.get("event") for r in records]
    assert "LAUNCHER_START" in events
    assert "LAUNCHER_SHUTDOWN" in events


@pytest.mark.asyncio
async def test_main_repeated_startup_shutdown_cleans_owned_handlers() -> None:
    """Repeated launcher runs remove owned handlers and restore the root level."""
    root = logging.getLogger()
    previous_level = root.level
    root.setLevel(logging.ERROR)

    try:
        for _ in range(3):
            exit_code = await async_main(["--status"])
            assert exit_code == 0
            owned = [
                handler
                for handler in root.handlers
                if getattr(handler, _OWNED_HANDLER_ATTR, False)
            ]
            assert owned == []
            assert root.level == logging.ERROR
    finally:
        root.setLevel(previous_level)


@pytest.mark.asyncio
async def test_main_failure_output_contains_no_canary_secret(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Launcher failure logs and output do not expose cleartext canary credentials."""
    canary = "super_secret_canary_key_12345"
    raw_path = f"nonexistent_token={canary}.toml"
    path_fingerprint = compute_secret_fingerprint(raw_path)

    exit_code = await async_main(["--config", raw_path])
    assert exit_code == 1

    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert canary not in combined
    assert raw_path not in combined
    assert path_fingerprint in captured.out
    assert path_fingerprint in captured.err


@pytest.mark.asyncio
async def test_main_shutdown_failure_still_cleans_handlers_and_secrets(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Engine shutdown failure returns nonzero without skipping logging cleanup."""
    canary = "shutdown_secret=engine_shutdown_canary_6442"

    async def fail_shutdown(_engine: object) -> None:
        raise RuntimeError(canary)

    monkeypatch.setattr("app.main.CompositionEngine.shutdown", fail_shutdown)
    exit_code = await async_main(["--status"])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert canary not in captured.out + captured.err
    assert compute_secret_fingerprint("engine_shutdown_canary_6442") in captured.err
    root = logging.getLogger()
    assert not any(
        getattr(handler, _OWNED_HANDLER_ATTR, False) for handler in root.handlers
    )


@pytest.mark.asyncio
async def test_main_logging_cleanup_failure_returns_nonzero_and_cleans(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Bounded logging cleanup diagnostics make launcher cleanup fail closed."""

    class CleanupFailureHandle:
        def __init__(self, config: LoggingConfig) -> None:
            self._real_handle = configure_logging(config)

        def close(self) -> tuple[CleanupDiagnostic, ...]:
            self._real_handle.close()
            return (
                CleanupDiagnostic(
                    stage="close",
                    handler_type="SyntheticHandler",
                    error_type="RuntimeError",
                ),
            )

    def configure_with_cleanup_failure(config: LoggingConfig) -> CleanupFailureHandle:
        return CleanupFailureHandle(config)

    monkeypatch.setattr("app.main.configure_logging", configure_with_cleanup_failure)
    exit_code = await async_main(["--status"])
    assert exit_code == 1
    captured = capsys.readouterr()
    json.loads(captured.out)
    assert "LOGGING_CLEANUP_FAILED" in captured.err
    assert "SyntheticHandler" in captured.err
    assert "RuntimeError" in captured.err
    assert not any(
        getattr(handler, _OWNED_HANDLER_ATTR, False)
        for handler in logging.getLogger().handlers
    )


@pytest.mark.asyncio
async def test_main_foreign_handler_raising_on_shutdown_logging_does_not_leak_owned_handlers(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A foreign handler raising on shutdown log events does not prevent owned handler cleanup."""

    class ShutdownRaisingHandler(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.raised = False

        @override
        def emit(self, record: logging.LogRecord) -> None:
            if getattr(record, "event", None) == "LAUNCHER_SHUTDOWN":
                self.raised = True
                raise RuntimeError("foreign_shutdown_secret=fail_on_shutdown_logging")

    foreign = ShutdownRaisingHandler()
    root = logging.getLogger()
    previous_level = root.level
    root.addHandler(foreign)
    try:
        exit_code = await async_main(["--status"])
        assert exit_code == 1
        assert foreign.raised is True
        assert not any(
            getattr(handler, _OWNED_HANDLER_ATTR, False) for handler in root.handlers
        )
        assert foreign in root.handlers
        captured = capsys.readouterr()
        json.loads(captured.out)
        assert "fail_on_shutdown_logging" not in captured.out + captured.err
    finally:
        root.removeHandler(foreign)
        root.setLevel(previous_level)


@pytest.mark.asyncio
async def test_main_toml_logging_config_and_cli_overrides(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """TOML [logging] section is respected and CLI arguments override TOML options."""
    toml_log_file = tmp_path / "toml_configured.log"
    cli_log_file = tmp_path / "cli_override.log"
    config_file = tmp_path / "app_with_logging.toml"
    config_file.write_text(
        f"""
        [application]
        profile = "research"

        [logging]
        level = "DEBUG"
        file_path = "{toml_log_file.as_posix()}"
        """,
        encoding="utf-8",
    )

    # 1. Run with config only (uses TOML log settings: DEBUG, toml_log_file)
    exit_code = await async_main(["--config", str(config_file), "--status"])
    assert exit_code == 0
    assert toml_log_file.is_file()
    toml_records = [
        json.loads(line)
        for line in toml_log_file.read_text(encoding="utf-8").strip().splitlines()
    ]
    assert any(r.get("event") == "LAUNCHER_START" for r in toml_records)

    # 2. Run with CLI overrides (overrides level to WARNING and file to cli_log_file)
    exit_code_override = await async_main(
        [
            "--config",
            str(config_file),
            "--log-level",
            "WARNING",
            "--log-file",
            str(cli_log_file),
            "--status",
        ]
    )
    assert exit_code_override == 0
    assert cli_log_file.is_file()
    cli_records = [
        json.loads(line)
        for line in cli_log_file.read_text(encoding="utf-8").strip().splitlines()
    ]
    # INFO events like LAUNCHER_START should NOT be in the file because level was overridden to WARNING
    assert not any(r.get("event") == "LAUNCHER_START" for r in cli_records)


@pytest.mark.asyncio
async def test_main_malformed_config_fails_cleanly(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Malformed TOML config returns exit code 1 with structured error logging."""
    bad_config = tmp_path / "bad.toml"
    bad_config.write_text("invalid = [ unclosed", encoding="utf-8")

    exit_code = await async_main(["--config", str(bad_config)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "[ERROR] Failed to parse configuration file" in captured.out
