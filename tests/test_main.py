"""Tests for main application entry point and composition bootstrap CLI."""

import json

import pytest

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
