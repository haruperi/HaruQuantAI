"""Unit tests for the canonical host response envelope and error taxonomy.

Covers:
    - FR-HOST-RESPONSE-SUCCESS-ENVELOPE: Success envelope construction and invariants.
    - FR-HOST-RESPONSE-ERROR-ENVELOPE: Error envelope construction and invariants.
    - FR-HOST-RESPONSE-SERIALIZATION: Dictionary transformation and JSON readiness.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from app.host.response import ResponseMetadata, StandardError, StandardResponse


def test_standard_response_success_defaults() -> None:
    """Verify success response with default arguments."""
    resp: StandardResponse[None] = StandardResponse.success()

    assert resp.is_success is True
    assert resp.is_error is False
    assert bool(resp) is True
    assert resp.data is None
    assert resp.message == "Operation completed successfully."
    assert resp.error is None
    assert resp.error_code is None
    assert resp.request_id is None
    assert resp.metadata.side_effects is False
    assert resp.metadata.duration_ms is None
    assert resp.metadata.extensions == {}
    assert resp.metadata.timestamp_utc != ""


def test_standard_response_success_with_payload() -> None:
    """Verify success response carrying typed data and explicit metadata."""
    data: dict[str, Any] = {"symbol": "EURUSD", "bid": 1.0850, "ask": 1.0852}
    resp: StandardResponse[dict[str, Any]] = StandardResponse.success(
        data=data,
        message="Market tick retrieved.",
        request_id="req-987",
        duration_ms=5.4,
        side_effects=True,
        extensions={"provider": "dukascopy"},
        timestamp_utc="2026-10-07T12:00:00Z",
    )

    assert resp.is_success is True
    assert resp.data == data
    assert resp.unwrap() == data
    assert resp.message == "Market tick retrieved."
    assert resp.request_id == "req-987"
    assert resp.metadata.duration_ms == 5.4
    assert resp.metadata.side_effects is True
    assert resp.metadata.extensions == {"provider": "dukascopy"}
    assert resp.metadata.timestamp_utc == "2026-10-07T12:00:00Z"


def test_standard_response_failure() -> None:
    """Verify failure response construction and error inspection."""
    err = StandardError(
        code="NETWORK_TIMEOUT",
        message="Connection to broker timed out.",
        details={"timeout_sec": 30},
        retryable=True,
    )
    resp: StandardResponse[None] = StandardResponse.failure(
        message="Execution aborted.",
        error=err,
        request_id="req-fail-001",
        duration_ms=30000.0,
        side_effects=False,
    )

    assert resp.is_success is False
    assert resp.is_error is True
    assert bool(resp) is False
    assert resp.data is None
    assert resp.error is err
    assert resp.error_code == "NETWORK_TIMEOUT"
    assert resp.request_id == "req-fail-001"
    assert resp.metadata.duration_ms == 30000.0


def test_standard_response_failure_unwrap_raises() -> None:
    """Verify unwrap raises RuntimeError on failure."""
    err = StandardError(code="INVALID_STATE", message="Engine is stopped.")
    resp: StandardResponse[str] = StandardResponse.failure(
        message="Failed operation.",
        error=err,
    )

    with pytest.raises(
        RuntimeError, match=r"Operation failed \[INVALID_STATE\]: Engine is stopped\."
    ):
        resp.unwrap()


def test_standard_response_failure_with_degraded_data() -> None:
    """Verify failure response can optionally carry degraded data."""
    err = StandardError(code="PARTIAL_READ", message="Stream truncated.")
    partial = ["chunk1", "chunk2"]
    resp: StandardResponse[list[str]] = StandardResponse.failure(
        message="Stream interrupted.",
        error=err,
        data=partial,
    )

    assert resp.is_error is True
    assert resp.data == partial
    with pytest.raises(RuntimeError, match=r"Operation failed \[PARTIAL_READ\]"):
        resp.unwrap()


def test_standard_response_invariants_status() -> None:
    """Verify invalid status string raises ValueError."""
    meta = ResponseMetadata(timestamp_utc="2026-10-07T12:00:00Z")
    with pytest.raises(ValueError, match="Invalid status 'pending'"):
        StandardResponse(
            status="pending",  # type: ignore[arg-type]
            message="Test",
            data=None,
            error=None,
            metadata=meta,
        )


def test_standard_response_invariants_success_with_error() -> None:
    """Verify success response containing error raises ValueError."""
    meta = ResponseMetadata(timestamp_utc="2026-10-07T12:00:00Z")
    err = StandardError(code="ERR", message="Err")
    with pytest.raises(ValueError, match="Success response must not contain an error"):
        StandardResponse(
            status="success",
            message="Test",
            data=None,
            error=err,
            metadata=meta,
        )


def test_standard_response_invariants_error_without_error() -> None:
    """Verify error response with error=None raises ValueError."""
    meta = ResponseMetadata(timestamp_utc="2026-10-07T12:00:00Z")
    with pytest.raises(
        ValueError, match="Error response must contain a StandardError instance"
    ):
        StandardResponse(
            status="error",
            message="Test",
            data=None,
            error=None,
            metadata=meta,
        )


def test_standard_response_invariants_error_wrong_type() -> None:
    """Verify error response with non-StandardError raises TypeError."""
    meta = ResponseMetadata(timestamp_utc="2026-10-07T12:00:00Z")
    with pytest.raises(TypeError, match="Error must be an instance of StandardError"):
        StandardResponse(
            status="error",
            message="Test",
            data=None,
            error="raw string",  # type: ignore[arg-type]
            metadata=meta,
        )


def test_standard_error_validation() -> None:
    """Verify StandardError attribute validation and defaults."""
    err = StandardError(code="AUTH_FAIL", message="Invalid token")
    assert err.code == "AUTH_FAIL"
    assert err.message == "Invalid token"
    assert err.details is None
    assert err.retryable is False

    with pytest.raises(ValueError, match="Error code must be a non-empty string"):
        StandardError(code="  ", message="Valid")

    with pytest.raises(ValueError, match="Error code must be a non-empty string"):
        StandardError(code="", message="Valid")

    with pytest.raises(ValueError, match="Error message must be a non-empty string"):
        StandardError(code="VALID", message="")

    with pytest.raises(ValueError, match="Error message must be a non-empty string"):
        StandardError(code="VALID", message=" \t ")


def test_response_metadata_validation() -> None:
    """Verify ResponseMetadata invariants."""
    meta = ResponseMetadata(
        timestamp_utc="2026-10-07T12:00:00Z",
        duration_ms=12.5,
        request_id="req-1",
        side_effects=False,
    )
    assert meta.duration_ms == 12.5
    assert meta.request_id == "req-1"

    with pytest.raises(ValueError, match="timestamp_utc must be a non-empty string"):
        ResponseMetadata(timestamp_utc="")

    with pytest.raises(ValueError, match="timestamp_utc must be a non-empty string"):
        ResponseMetadata(timestamp_utc="   ")

    with pytest.raises(ValueError, match="duration_ms cannot be negative"):
        ResponseMetadata(timestamp_utc="2026-10-07T12:00:00Z", duration_ms=-0.1)


def test_to_dict_serialization() -> None:
    """Verify to_dict returns JSON-serializable dictionary with expected structure."""
    resp = StandardResponse.success(
        data={"items": [1, 2, 3]},
        message="Serialized ok",
        request_id="req-json",
        duration_ms=2.1,
    )
    d = resp.to_dict()

    assert d["status"] == "success"
    assert d["message"] == "Serialized ok"
    assert d["data"] == {"items": [1, 2, 3]}
    assert d["error"] is None
    assert d["request_id"] == "req-json"
    assert d["metadata"]["request_id"] == "req-json"
    assert d["metadata"]["duration_ms"] == 2.1

    # Verify JSON encoding
    encoded = json.dumps(d)
    assert "req-json" in encoded


def test_to_dict_failure_serialization() -> None:
    """Verify failure response to_dict serialization."""
    err = StandardError(code="E1", message="Failure", details={"attempt": 1})
    resp = StandardResponse.failure(message="Failed", error=err, request_id="req-err")
    d = resp.to_dict()

    assert d["status"] == "error"
    assert d["error"]["code"] == "E1"
    assert d["error"]["details"] == {"attempt": 1}
    assert d["request_id"] == "req-err"


def test_to_dict_without_request_id() -> None:
    """Verify to_dict when request_id is None."""
    resp = StandardResponse.success(data="test", message="no req id")
    d = resp.to_dict()
    assert d["status"] == "success"
    assert "request_id" not in d
    assert d["metadata"]["request_id"] is None


def test_response_logging_emissions() -> None:
    """Verify telemetry log emissions for success, failure, and to_dict."""
    from app.host.logging import TelemetryEngine

    engine = TelemetryEngine.get_or_create()

    # Success log
    resp = StandardResponse.success(
        data=42,
        message="Logged success",
        duration_ms=1.5,
        request_id="req-log-1",
    )
    # Failure log
    err = StandardError(code="ERR_LOG", message="Logged err")
    _ = StandardResponse.failure(
        message="Logged failure",
        error=err,
        request_id="req-log-2",
    )
    # Serialization log
    resp.to_dict()

    requirements = [e.context.get("requirement") for e in engine.ring_buffer._entries]

    assert "FR-HOST-RESPONSE-SUCCESS-ENVELOPE" in requirements
    assert "FR-HOST-RESPONSE-ERROR-ENVELOPE" in requirements
    assert "FR-HOST-RESPONSE-SERIALIZATION" in requirements
