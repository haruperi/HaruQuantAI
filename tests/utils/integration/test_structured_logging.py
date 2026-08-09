import json
import os
import time
import zipfile
from pathlib import Path

import pytest
from app.utils import (
    configure_logging,
    flush_logging,
    get_logger,
    log_info,
    shutdown_logging,
)

logger = get_logger(__name__)


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
    configure_logging()
    log_info(
        logger,
        "api_key=abc123",
        context={"request_id": "req-example", "password": "hidden"},
    )
    log_info(logger, "access", context={"log_type": "access"})
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


def test_zip_rollover_and_shutdown(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify real compression, retention, queued delivery, and shutdown IO."""
    monkeypatch.setenv("LOG_DIRECTORY", str(tmp_path))
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_RENDER", "json")
    monkeypatch.setenv("LOG_MAX_BYTES", "1024")
    monkeypatch.setenv("LOG_BACKUP_COUNT", "10")
    monkeypatch.setenv("LOG_RETENTION_DAYS", "10")
    monkeypatch.setenv("LOG_COMPRESSION", "zip")
    monkeypatch.setenv("LOG_ENQUEUE", "true")
    monkeypatch.setenv("LOG_COLORIZE", "false")
    shutdown_logging()
    configure_logging()
    expired = tmp_path / "app.log.9.zip"
    expired.write_text("expired", encoding="utf-8")
    old_timestamp = time.time() - (11 * 86_400)
    os.utime(expired, (old_timestamp, old_timestamp))
    for index in range(30):
        logger.debug("rollover %s %s", index, "x" * 200)
    shutdown_logging()

    archives = sorted(tmp_path.glob("app.log.*.zip"))
    assert archives
    assert all(zipfile.is_zipfile(archive) for archive in archives)
    cutoff = time.time() - (10 * 86_400)
    assert all(archive.stat().st_mtime >= cutoff for archive in archives)
