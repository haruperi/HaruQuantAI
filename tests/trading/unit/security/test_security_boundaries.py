"""Unit tests for trading security error mapping and redaction boundaries."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.trading.contracts import JsonObject
from app.services.trading.security import (
    DeadLetterRecord,
    TradingMappedError,
    TradingPermissionError,
    TradingServiceUnavailableError,
    TradingTimeoutError,
    TradingValidationError,
    WriteAheadDeadLetterQueue,
    map_exception_to_trading_error,
    redact_for_boundary,
)
from pydantic import ValidationError as PydanticValidationError


class FixedClock:
    """Fixed test clock."""

    def now_utc(self) -> datetime:
        """Return a fixed UTC timestamp."""
        return datetime(2026, 7, 9, 12, 0, tzinfo=UTC)

    def now_ptp(self) -> datetime:
        """Return a fixed PTP timestamp."""
        return datetime(2026, 7, 9, 12, 0, tzinfo=UTC)

    def monotonic(self) -> float:
        """Return a fixed monotonic value."""
        return 12.0


def test_trading_exception_hierarchy_maps_standard_codes() -> None:
    """Trading-specific exceptions inherit the base and map public codes."""
    errors = (
        (TradingValidationError("bad token=secret"), "VALIDATION_FAILED"),
        (TradingTimeoutError("timeout"), "TIMEOUT"),
        (TradingPermissionError("auth failed"), "PERMISSION_DENIED"),
        (TradingServiceUnavailableError("broker down"), "BROKER_UNAVAILABLE"),
        (TradingMappedError("custom", code="DATABASE_ERROR"), "DATABASE_ERROR"),
    )

    for raw_error, code in errors:
        mapped = map_exception_to_trading_error(
            raw_error,
            request_id="req-1",
            correlation_id="corr-1",
            provider="mt5",
        )

        assert isinstance(raw_error, TradingMappedError)
        assert mapped.code == code
        assert "req-1" in mapped.details
        assert "corr-1" in mapped.details
        assert "secret" not in mapped.details


@pytest.mark.parametrize(
    ("raw_error", "code"),
    [
        (TimeoutError("timed out token=secret"), "TIMEOUT"),
        (PermissionError("permission denied"), "PERMISSION_DENIED"),
        (ConnectionError("connection failed"), "BROKER_UNAVAILABLE"),
        (OSError("socket issue"), "NETWORK_ERROR"),
        (ValueError("bad input"), "VALIDATION_FAILED"),
        (Exception("database write failed"), "DATABASE_ERROR"),
        (Exception("auth rejected"), "PERMISSION_DENIED"),
        (Exception("timeout waiting"), "TIMEOUT"),
        (Exception("network broker down"), "BROKER_UNAVAILABLE"),
        (Exception("unknown"), "UNKNOWN_ERROR"),
    ],
)
def test_raw_exceptions_map_without_raw_trace_or_secret(
    raw_error: BaseException,
    code: str,
) -> None:
    """Raw exceptions map to standard public codes and redacted details."""
    mapped = map_exception_to_trading_error(
        raw_error,
        request_id="req-2",
        correlation_id="corr-2",
    )

    assert mapped.code == code
    assert "Traceback" not in mapped.details
    assert "secret" not in mapped.details


def test_pydantic_validation_maps_to_validation_failed() -> None:
    """Pydantic validation errors map to validation failures."""
    with pytest.raises(PydanticValidationError) as error_info:
        DeadLetterRecord(
            event_id="event",
            source="source",
            reason="reason",
            payload={},
            max_retries=0,
            written_at="2026-07-09T12:00:00+00:00",
        )

    mapped = map_exception_to_trading_error(
        error_info.value,
        request_id="req-3",
        correlation_id="corr-3",
    )

    assert mapped.code == "VALIDATION_FAILED"


def test_map_exception_requires_request_and_correlation_ids() -> None:
    """Blank identifiers are rejected before public mapping."""
    with pytest.raises(ValueError, match="request_id"):
        map_exception_to_trading_error(
            Exception("boom"),
            request_id=" ",
            correlation_id="corr",
        )

    with pytest.raises(ValueError, match="correlation_id"):
        map_exception_to_trading_error(
            Exception("boom"),
            request_id="req",
            correlation_id=" ",
        )


def test_redact_for_boundary_recursively_redacts_and_alerts() -> None:
    """Boundary redaction handles nested secrets and private account details."""
    result = redact_for_boundary(
        {
            "account": "demo",
            "nested": {"API_KEY": "abcdefabcdefabcdefabcdefabcdef12"},
            "items": [{"password": "raw"}],
        },
        blocked_live_scopes=("strategy-a",),
        alert_message="password=hidden",
    )

    rendered = str(result.payload)
    assert "abcdef" not in rendered
    assert "raw" not in rendered
    assert result.payload["nested"] == {"API_KEY": "[REDACTED]"}
    assert result.blocked_live_scopes == ("strategy-a",)
    assert result.alert is not None
    assert result.alert["severity"] == "high"
    assert "hidden" not in str(result.alert)


def test_write_failed_event_persists_redacted_jsonl(tmp_path: Path) -> None:
    """DLQ writes redacted payloads to a durable write-ahead JSONL file."""
    queue = WriteAheadDeadLetterQueue(
        path=tmp_path / "dlq.jsonl",
        manual_review_path=tmp_path / "manual.jsonl",
        clock=FixedClock(),
        max_retries=2,
    )

    result = queue.write_failed_event(
        source="broker_event",
        reason="parse failed password=raw",
        payload={"token": "abcdefabcdefabcdefabcdefabcdef12", "value": 1},
        affected_live_scopes=("live:EURUSD",),
    )

    text = (tmp_path / "dlq.jsonl").read_text(encoding="utf-8")
    assert result.record.event_id in text
    assert "abcdef" not in text
    assert "raw" not in text
    assert result.alert["severity"] == "high"
    assert result.blocked_live_scopes == ("live:EURUSD",)
    assert queue.read_pending()[0].event_id == result.record.event_id


def test_dlq_recovery_is_exactly_once_for_success(tmp_path: Path) -> None:
    """Successful recovery removes the record from the pending log."""
    queue = WriteAheadDeadLetterQueue(
        path=tmp_path / "dlq.jsonl",
        manual_review_path=tmp_path / "manual.jsonl",
        clock=FixedClock(),
    )
    written = queue.write_failed_event(
        source="audit",
        reason="persist failed",
        payload={"safe": "value"},
        affected_live_scopes=("scope",),
    )
    calls: list[object] = []

    def process_once(payload: JsonObject) -> bool:
        """Record payload processing and report success."""
        calls.append(payload)
        return True

    recovered = queue.recover_pending(processor=process_once)

    assert recovered == (written.record.event_id,)
    assert calls == [{"safe": "value"}]
    assert queue.read_pending() == ()


def test_dlq_failed_recovery_retries_then_manual_review(tmp_path: Path) -> None:
    """Poison-pill records move to manual review after retry threshold."""
    queue = WriteAheadDeadLetterQueue(
        path=tmp_path / "dlq.jsonl",
        manual_review_path=tmp_path / "manual.jsonl",
        clock=FixedClock(),
        max_retries=2,
    )
    written = queue.write_failed_event(
        source="audit",
        reason="persist failed",
        payload={"safe": "value"},
        affected_live_scopes=("scope",),
    )

    def fail_processing(payload: JsonObject) -> bool:
        """Use the payload path while reporting failed processing."""
        return "safe" in payload and False

    first = queue.recover_pending(processor=fail_processing)
    second = queue.recover_pending(processor=fail_processing)

    assert first == ()
    assert second == ()
    assert queue.read_pending() == ()
    manual = queue.read_manual_review()
    assert manual[0].record.event_id == written.record.event_id
    assert manual[0].record.retry_count == 2
    assert manual[0].alert["severity"] == "high"


def test_dlq_validation_and_corruption_paths(tmp_path: Path) -> None:
    """DLQ rejects invalid setup, blank fields, and corrupt persisted JSON."""
    with pytest.raises(ValueError, match="max_retries"):
        WriteAheadDeadLetterQueue(
            path=tmp_path / "dlq.jsonl",
            manual_review_path=tmp_path / "manual.jsonl",
            clock=FixedClock(),
            max_retries=0,
        )

    queue = WriteAheadDeadLetterQueue(
        path=tmp_path / "dlq.jsonl",
        manual_review_path=tmp_path / "manual.jsonl",
        clock=FixedClock(),
    )
    with pytest.raises(ValueError, match="source"):
        queue.write_failed_event(
            source=" ",
            reason="reason",
            payload={"safe": "value"},
            affected_live_scopes=("scope",),
        )
    with pytest.raises(ValueError, match="reason"):
        queue.write_failed_event(
            source="source",
            reason=" ",
            payload={"safe": "value"},
            affected_live_scopes=("scope",),
        )
    with pytest.raises(ValueError, match="blank"):
        queue.write_failed_event(
            source="source",
            reason="reason",
            payload={"safe": "value"},
            affected_live_scopes=(" ",),
        )

    (tmp_path / "dlq.jsonl").write_text("{bad", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        queue.read_pending()
