"""Tests for application bootstrap."""

import json

import pytest

from app.main import run, run_async


@pytest.mark.asyncio
async def test_run_async_boots_live_shell_with_degraded_research_readiness() -> None:
    status = await run_async()
    assert status["liveness"] == {"live": True, "status": "OK"}
    readiness = status["readiness"]
    assert isinstance(readiness, dict)
    assert readiness["ready"] is False
    assert "data.historical-bars@1" in readiness["missing_capabilities"]


def test_app_run_prints_machine_readable_status(
    capsys: pytest.CaptureFixture[str],
) -> None:
    run()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["liveness"]["live"] is True
    assert payload["readiness"]["profile"] == "research"
