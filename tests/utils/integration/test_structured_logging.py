import json
from pathlib import Path

from app.utils import (
    LoggingSettings,
    configure_logging,
    get_logger,
    shutdown_logging,
)


def test_structured_logging_redacts_before_file_emission(tmp_path: Path) -> None:
    log_path = tmp_path / "app.log"
    configure_logging(
        LoggingSettings(file_path=log_path, log_directory=None, render="json")
    )
    logger = get_logger("integration")
    logger.info(
        "token=abc123",
        extra={"request_id": "req-example", "password": "hidden"},
    )
    shutdown_logging()
    record = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert record["message"] == "token=[REDACTED]"
    assert record["request_id"] == "req-example"
    assert "abc123" not in repr(record)
    assert "hidden" not in repr(record)
