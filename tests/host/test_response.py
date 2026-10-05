"""Unit tests for the standard host response envelope.

Verifies FEAT-HOST-RESPONSE capabilities including StandardError,
ResponseMetadata, and StandardResponse invariants, factories, and telemetry
logging.
"""

from __future__ import annotations

import json
import logging
from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path
from typing import Any

import pytest
from app.host.logging import configure_host_logging, flush, reset_logging
from app.host.response import (
    ResponseMetadata,
    StandardError,
    StandardResponse,
    _now_utc_iso,
)


@dataclass(frozen=True, slots=True)
class _SamplePayload:
    symbol: str
    price: float


def test_standard_error_initialization_and_immutability() -> None:
    """Verify StandardError creation, attributes, defaults, and immutability."""
    err = StandardError(
        code="VALIDATION_FAILED",
        message="Parameter out of bounds.",
        details={"field": "volume", "min": 0.01},
        retryable=True,
    )
    assert err.code == "VALIDATION_FAILED"
    assert err.message == "Parameter out of bounds."
    assert err.details == {"field": "volume", "min": 0.01}
    assert err.retryable is True

    # Test defaults
    default_err = StandardError(code="ERR_GENERIC", message="Something went wrong.")
    assert default_err.details is None
    assert default_err.retryable is False

    # Test frozen immutability
    with pytest.raises(FrozenInstanceError):
        err.code = "NEW_CODE"  # type: ignore[misc]


def test_standard_error_validation_rejections() -> None:
    """Verify StandardError rejects empty or whitespace-only code and message."""
    with pytest.raises(ValueError, match=r"^Error code must be a non-empty string\.$"):
        StandardError(code="", message="Valid message")

    with pytest.raises(ValueError, match=r"^Error code must be a non-empty string\.$"):
        StandardError(code="   ", message="Valid message")

    with pytest.raises(
        ValueError, match=r"^Error message must be a non-empty string\.$"
    ):
        StandardError(code="ERR_CODE", message="")

    with pytest.raises(
        ValueError, match=r"^Error message must be a non-empty string\.$"
    ):
        StandardError(code="ERR_CODE", message="   ")


def test_response_metadata_initialization_and_immutability() -> None:
    """Verify ResponseMetadata creation, attributes, defaults, and immutability."""
    ts = _now_utc_iso()
    meta = ResponseMetadata(
        timestamp_utc=ts,
        duration_ms=12.5,
        request_id="req-999",
        side_effects=True,
        extensions={"worker": "proc-1"},
    )
    assert meta.timestamp_utc == ts
    assert meta.duration_ms == 12.5
    assert meta.request_id == "req-999"
    assert meta.side_effects is True
    assert meta.extensions == {"worker": "proc-1"}

    # Test defaults
    default_meta = ResponseMetadata(timestamp_utc=ts)
    assert default_meta.duration_ms is None
    assert default_meta.request_id is None
    assert default_meta.side_effects is False
    assert default_meta.extensions == {}

    # Test frozen immutability
    with pytest.raises(FrozenInstanceError):
        meta.side_effects = False  # type: ignore[misc]


def test_response_metadata_validation_rejections() -> None:
    """Verify ResponseMetadata rejects invalid duration or timestamp."""
    with pytest.raises(
        ValueError, match=r"^timestamp_utc must be a non-empty string\.$"
    ):
        ResponseMetadata(timestamp_utc="")

    with pytest.raises(
        ValueError, match=r"^timestamp_utc must be a non-empty string\.$"
    ):
        ResponseMetadata(timestamp_utc="   ")

    with pytest.raises(ValueError, match=r"^duration_ms cannot be negative"):
        ResponseMetadata(timestamp_utc=_now_utc_iso(), duration_ms=-1.0)


def test_standard_response_success_factory() -> None:
    """Verify StandardResponse.success and ok factory creation."""
    payload = {"symbol": "BTCUSD", "qty": 1.5}
    resp: StandardResponse[dict[str, Any]] = StandardResponse.success(
        data=payload,
        message="Order placed successfully.",
        request_id="req-abc",
        duration_ms=45.2,
        side_effects=True,
        extensions={"broker": "binance"},
        timestamp_utc="2026-10-05T08:00:00Z",
    )

    assert resp.status == "success"
    assert resp.is_success is True
    assert resp.is_error is False
    assert resp.message == "Order placed successfully."
    assert resp.data == payload
    assert resp.error is None
    assert resp.metadata.request_id == "req-abc"
    assert resp.metadata.duration_ms == 45.2
    assert resp.metadata.side_effects is True
    assert resp.metadata.extensions == {"broker": "binance"}
    assert resp.metadata.timestamp_utc == "2026-10-05T08:00:00Z"


def test_standard_response_failure_factory() -> None:
    """Verify StandardResponse.failure factory creation and attributes."""
    err = StandardError(
        code="NETWORK_TIMEOUT",
        message="Gateway did not respond in 5000ms.",
        details={"timeout_ms": 5000},
        retryable=True,
    )
    resp: StandardResponse[None] = StandardResponse.failure(
        message="Request timed out.",
        error=err,
        request_id="req-xyz",
        duration_ms=5002.1,
        side_effects=False,
    )

    assert resp.status == "error"
    assert resp.is_success is False
    assert resp.is_error is True
    assert resp.message == "Request timed out."
    assert resp.data is None
    assert resp.error == err
    assert resp.metadata.request_id == "req-xyz"
    assert resp.metadata.duration_ms == 5002.1


def test_standard_response_structural_invariants() -> None:
    """Verify StandardResponse rejects invalid status or mismatched errors."""
    meta = ResponseMetadata(timestamp_utc=_now_utc_iso())
    err = StandardError(code="ERR_FAIL", message="Failed.")

    # Invalid status
    with pytest.raises(ValueError, match=r"^Invalid status 'unknown'"):
        StandardResponse(
            status="unknown",  # type: ignore[arg-type]
            message="Test",
            data=None,
            error=None,
            metadata=meta,
        )

    # Success carrying an error
    with pytest.raises(
        ValueError, match=r"^Success response must not contain an error\.$"
    ):
        StandardResponse(
            status="success",
            message="Test",
            data={"value": 1},
            error=err,
            metadata=meta,
        )

    # Error without an error object
    with pytest.raises(
        ValueError,
        match=r"^Error response must contain a StandardError instance\.$",
    ):
        StandardResponse(
            status="error",
            message="Test",
            data=None,
            error=None,
            metadata=meta,
        )

    # Error with wrong type
    with pytest.raises(TypeError, match=r"^Error must be an instance of StandardError"):
        StandardResponse(
            status="error",
            message="Test",
            data=None,
            error="NotAStandardError",  # type: ignore[arg-type]
            metadata=meta,
        )


def test_standard_response_serialization_and_json() -> None:
    """Verify to_dict serialization and JSON encode compatibility."""
    payload = _SamplePayload(symbol="ETHUSD", price=3200.50)
    resp = StandardResponse.success(
        data=payload,
        message="Ticker loaded.",
        duration_ms=1.2,
        request_id="req-ser-1",
    )

    serialized = resp.to_dict()
    assert isinstance(serialized, dict)
    assert serialized["status"] == "success"
    assert serialized["message"] == "Ticker loaded."
    assert serialized["data"] == {"symbol": "ETHUSD", "price": 3200.50}
    assert serialized["error"] is None
    assert serialized["metadata"]["duration_ms"] == 1.2
    assert serialized["metadata"]["request_id"] == "req-ser-1"

    # Verify JSON serializability
    json_str = json.dumps(serialized)
    assert "ETHUSD" in json_str


def test_standard_response_error_serialization() -> None:
    """Verify to_dict serialization on error responses."""
    err = StandardError(
        code="UNAUTHORIZED",
        message="Invalid token.",
        details={"token_length": 12},
        retryable=False,
    )
    resp = StandardResponse.failure(message="Access denied.", error=err)
    serialized = resp.to_dict()

    assert serialized["status"] == "error"
    assert serialized["error"]["code"] == "UNAUTHORIZED"
    assert serialized["error"]["message"] == "Invalid token."
    assert serialized["error"]["details"] == {"token_length": 12}
    assert serialized["error"]["retryable"] is False
    assert json.dumps(serialized)


def test_response_telemetry_logging_requirements(tmp_path: Path) -> None:
    """Verify non-silent logging for FR-HOST-RESPONSE capabilities."""
    log_dir = tmp_path / "telemetry_logs"
    configure_host_logging(log_dir=log_dir, level=logging.DEBUG, include_console=False)
    try:
        # Trigger FR-HOST-RESPONSE-SUCCESS-ENVELOPE
        success_resp = StandardResponse.success(
            data={"val": 42},
            message="Telemetry success test.",
            request_id="req-tel-1",
            duration_ms=10.5,
        )

        # Trigger FR-HOST-RESPONSE-ERROR-ENVELOPE
        err = StandardError(code="FEED_ERR", message="Feed drop.")
        error_resp = StandardResponse.failure(
            message="Telemetry error test.",
            error=err,
            request_id="req-tel-2",
        )

        # Trigger FR-HOST-RESPONSE-SERIALIZATION
        _ = success_resp.to_dict()
        _ = error_resp.to_dict()

        flush()

        app_log = log_dir / "app.log"
        assert app_log.exists()
        lines = [
            json.loads(line)
            for line in app_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        # 1. Check success requirement log
        success_events = [
            e
            for e in lines
            if e.get("context", {}).get("requirement")
            == "FR-HOST-RESPONSE-SUCCESS-ENVELOPE"
        ]
        assert len(success_events) >= 1
        assert "Telemetry success test." in success_events[0]["message"]

        # 2. Check error requirement log
        error_events = [
            e
            for e in lines
            if e.get("context", {}).get("requirement")
            == "FR-HOST-RESPONSE-ERROR-ENVELOPE"
        ]
        assert len(error_events) >= 1
        assert "FEED_ERR" in error_events[0]["message"]

        # 3. Check serialization requirement log
        serial_events = [
            e
            for e in lines
            if e.get("context", {}).get("requirement")
            == "FR-HOST-RESPONSE-SERIALIZATION"
        ]
        assert len(serial_events) >= 2
    finally:
        reset_logging()
