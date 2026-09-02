"""Unit tests for app/contracts/common/models.py helper functions and response builders."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

from app.contracts.common.models import (
    AuthContext,
    StandardResponse,
    ValidationOutcome,
    build_event_envelope,
    build_health_state,
    build_reservation,
    build_response_metadata,
    build_validation_outcome,
    create_audit_event,
    create_auth_context,
    derive_idempotency_key,
    error_response,
    evaluate_reservation,
    exception_response,
    find_sequence_gap,
    get_audit_event_type,
    get_auth_context_type,
    get_execution_ms,
    get_standard_response_type,
    is_duplicate_event,
    is_reservation_expired,
    parse_event_envelope,
    parse_health_state,
    parse_idempotency_key,
    success_response,
    validate_reason_code,
)


def test_build_response_metadata_and_execution_time() -> None:
    """Verify build_response_metadata calculates elapsed time and defaults correctly."""
    t0 = time.perf_counter_ns()
    time.sleep(0.002)
    meta = build_response_metadata(
        request_id="01918a99-0000-7000-8000-000000000001",
        start_time=t0,
        name="test_op",
        domain="market",
    )
    assert meta.request_id == "01918a99-0000-7000-8000-000000000001"
    assert meta.execution_ms > 0.0
    assert meta.domain == "market"
    assert meta.risk_level == "none"

    # Direct execution_ms override
    meta2 = build_response_metadata(
        request_id="01918a99-0000-7000-8000-000000000002",
        execution_ms=12.345,
    )
    assert meta2.execution_ms == 12.345

    elapsed = get_execution_ms(t0)
    assert elapsed > 0.0


def test_standard_response_constructors() -> None:
    """Verify success_response, error_response, and exception_response envelopes."""
    meta = build_response_metadata(request_id="01918a99-0000-7000-8000-000000000001")

    # Success
    resp_success = success_response({"status": "ok"}, message="All good", metadata=meta)
    assert resp_success.status == "success"
    assert resp_success.data == {"status": "ok"}
    assert resp_success.message == "All good"

    # Error
    resp_err = error_response(
        code="INVALID_PARAMETER",
        message="Invalid volume",
        metadata=meta,
        details={"volume": "must be positive"},
        status=422,
    )
    assert resp_err.status == "error"
    assert resp_err.error is not None
    assert resp_err.error.code == "INVALID_PARAMETER"
    assert resp_err.error.status == 422
    assert len(resp_err.error.errors) == 1

    # Exception
    exc = ValueError("Fatal crash")
    resp_exc = exception_response(exc, metadata=meta)
    assert resp_exc.status == "exception"
    assert resp_exc.error is not None
    assert resp_exc.error.status == 500
    assert resp_exc.error.title == "ValueError"

    assert get_standard_response_type() == StandardResponse


def test_auth_context_and_audit_event_builders() -> None:
    """Verify create_auth_context and create_audit_event builders."""
    auth = create_auth_context(
        principal_id="user-123",
        principal_type="USER",
        roles=("admin",),
        permissions=("trade:execute",),
        issued_at=datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC),
    )
    assert isinstance(auth, AuthContext)
    assert auth.principal_id == "user-123"
    assert auth.roles == ("admin",)
    assert get_auth_context_type() == AuthContext

    audit = create_audit_event(
        domain="order",
        action="PLACE_ORDER",
        payload={"order_id": "ord-1"},
        occurred_at=datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC),
        principal_id="user-123",
    )
    assert audit.domain == "order"
    assert audit.action == "PLACE_ORDER"
    assert audit.payload == {"order_id": "ord-1"}
    assert get_audit_event_type() == audit.__class__


def test_event_envelope_and_helpers() -> None:
    """Verify event envelope creation, deduplication, and gap detection."""
    env = build_event_envelope(
        event_id="evt-100",
        source_id="src-1",
        payload={"tick": 1},
        emitted_at=datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC),
    )
    assert env["event_id"] == "evt-100"
    assert env["source_id"] == "src-1"
    assert parse_event_envelope(env) == env

    # Sequence gaps
    assert find_sequence_gap([1, 2, 3, 5]) == 4
    assert find_sequence_gap([1, 2, 3, 4]) is None

    # Deduplication
    seen: set[str] = set()
    assert is_duplicate_event(seen, "key-1") is False
    assert is_duplicate_event(seen, "key-1") is True


def test_validation_outcome_and_health_and_idempotency() -> None:
    """Verify validation outcome, health state, and idempotency key builders."""
    out = build_validation_outcome(
        verdict="PASS",
        check_id="check-risk",
        reason_codes=["RISK_OK.VALID"],
    )
    assert isinstance(out, ValidationOutcome)
    assert out.verdict == "PASS"
    assert validate_reason_code("RISK_OK.VALID") is True
    assert validate_reason_code("NO_DOT") is False

    # Health state
    health = build_health_state(
        dependency="postgres",
        category="DATABASE",
        state="HEALTHY",
        observed_at=datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC),
    )
    assert health["dependency"] == "postgres"
    assert parse_health_state(health) == health

    # Idempotency
    future_time = datetime.now(UTC) + timedelta(hours=1)
    res = build_reservation(key="k1", owner_id="node1", expires_at=future_time)
    assert evaluate_reservation(res) is True
    assert is_reservation_expired(res) is False

    past_time = datetime.now(UTC) - timedelta(hours=1)
    past_res = build_reservation(key="k2", owner_id="node1", expires_at=past_time)
    assert evaluate_reservation(past_res) is False
    assert is_reservation_expired(past_res) is True

    key = derive_idempotency_key("order", "user1", "sym1")
    assert key.startswith("order-")
    assert parse_idempotency_key("  clean_key  ") == "clean_key"
