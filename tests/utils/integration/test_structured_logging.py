import json
from pathlib import Path

import pytest
from app.utils import (
    flush_logging,
    logger,
    shutdown_logging,
)


def test_structured_logging_redacts_before_file_emission(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Route redacted records through the real specialized file sinks."""
    monkeypatch.setenv("LOG_DIRECTORY", str(tmp_path))
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_RENDER", "json")
    monkeypatch.setenv("LOG_COLORIZE", "false")
    shutdown_logging()
    logger.bind(request_id="req-example", password="hidden").info("api_key=abc123")
    logger.bind(log_type="access").info("access")
    logger.debug("debug")
    logger.error("error")
    flush_logging()
    shutdown_logging()
    records = [
        json.loads(line)
        for line in (tmp_path / "app.log").read_text(encoding="utf-8").splitlines()
    ]
    record = records[0]
    assert record["message"] == "api_key=[REDACTED]"
    assert record["request_id"] == "req-example"
    assert "abc123" not in repr(record)
    assert "hidden" not in repr(record)
    assert (tmp_path / "access.log").read_text(encoding="utf-8")
    assert (tmp_path / "debug.log").read_text(encoding="utf-8")
    assert (tmp_path / "errors.log").read_text(encoding="utf-8")
