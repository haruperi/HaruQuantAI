"""Focused branch coverage for Utils Phase 0 fail-closed boundaries."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.utils import (
    attempt_transition,
    build_event_envelope,
    build_exact_unit,
    build_health_state,
    build_profile_ref,
    build_reservation,
    build_time_stamp,
    build_transition_record,
    build_transition_table,
    build_validation_outcome,
    compare_time_stamps,
    derive_idempotency_key,
    derive_random_stream,
    evaluate_reservation,
    find_sequence_gap,
    from_venue_local,
    get_key_owner,
    get_severity_rank,
    is_duplicate_event,
    is_reservation_expired,
    load_profile_document,
    next_choice,
    next_int,
    next_sequence,
    next_uniform,
    parse_event_envelope,
    parse_health_state,
    parse_idempotency_key,
    parse_time_stamp,
    parse_validation_outcome,
    quantize_exact,
    route_audit_event,
    scale_exact,
    subtract_exact,
    to_venue_local,
    unit_kind_requires_currency,
    validate_reason_code,
)
from app.utils.errors.contracts import ErrorDefinition
from app.utils.errors.exceptions import ConfigurationError, ValidationError
from app.utils.errors.validation import validate_error_catalog

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_reference_and_health_edge_paths() -> None:
    document, reference = load_profile_document(
        {"profile_kind": "risk", "profile_id": "p", "version": "1", "limit": 1},
        required_fields=["limit"],
        compatible_versions=["1"],
    )
    assert document["limit"] == 1
    assert reference["content_hash"]
    with pytest.raises(ConfigurationError):
        load_profile_document(
            {"profile_kind": "risk"},
            required_fields=["limit"],
            compatible_versions=["1"],
        )
    with pytest.raises(ConfigurationError):
        load_profile_document(
            {"profile_kind": "risk", "profile_id": "p", "version": "2", "limit": 1},
            required_fields=["limit"],
            compatible_versions=["1"],
        )
    health = build_health_state(
        dependency="feed",
        category="DATA_STALE",
        state="DEGRADED",
        retryable=True,
        operator_action="Refresh",
        observed_at=NOW,
    )
    assert parse_health_state(health) == health
    with pytest.raises(ValidationError):
        parse_health_state({})


def test_time_sequence_and_conversion_edge_paths() -> None:
    stamp = build_time_stamp(domain="FILL", instant=NOW)
    assert parse_time_stamp(stamp) == stamp
    assert compare_time_stamps(stamp, stamp) == 0
    local = to_venue_local(NOW, "UTC")
    assert local["utc"].endswith("Z")
    assert from_venue_local("2026-01-01T00:00:00", "UTC") == NOW
    counter: dict[str, int] = {}
    assert (next_sequence("events", counter), next_sequence("events", counter)) == (
        0,
        1,
    )
    assert next_sequence("events", lambda _: 8) == 8
    with pytest.raises(ValidationError):
        next_sequence("", counter)
    with pytest.raises(ValidationError):
        to_venue_local(NOW.replace(tzinfo=None), "UTC")


def test_envelope_duplicate_gap_and_validation_paths() -> None:
    envelope = build_event_envelope(
        event_id="evt",
        source_id="sim",
        source_sequence=3,
        correlation_id="cor",
        causation_id="cau",
        deduplication_key="key",
        emitted_at=NOW,
        payload={"value": 1},
    )
    assert not is_duplicate_event(envelope, set())
    assert find_sequence_gap(envelope, expected_sequence=1) == {
        "expected_sequence": 1,
        "actual_sequence": 3,
        "missing_count": 2,
    }
    assert find_sequence_gap(envelope, expected_sequence=3) is None
    broken = dict(envelope)
    broken["contract_version"] = "v2"
    with pytest.raises(ValidationError):
        parse_event_envelope(broken)


def test_units_transition_and_audit_edge_paths() -> None:
    value = build_exact_unit("2.5", kind="QUANTITY")
    assert (
        subtract_exact(value, build_exact_unit("1", kind="QUANTITY"))["amount"] == "1.5"
    )
    assert scale_exact(value, Decimal(2))["amount"] == "5.0"
    assert quantize_exact(value, "1", direction="UP")["amount"] == "3"
    assert unit_kind_requires_currency("MONEY")
    with pytest.raises(ValidationError):
        build_exact_unit("1", kind="MONEY")
    table = build_transition_table(
        {"A": ["B"], "B": ["C"], "C": []},
        terminal_states=["C"],
        ranks={"A": 0, "B": 1, "C": 2},
    )
    assert attempt_transition(table, "A", "C")["outcome"] == "REJECTED_UNDECLARED_EDGE"
    assert (
        build_transition_record(
            entity_id="ord",
            source_state="A",
            target_state="B",
            outcome="ACCEPTED",
            reason_code="EDGE_DECLARED",
            actor_ref="user",
            occurred_at=NOW,
            sequence=1,
        )["sequence"]
        == 1
    )
    with pytest.raises(ValidationError):
        build_transition_table({"A": ["A"]}, terminal_states=["A"])


def test_validation_and_reason_edge_paths() -> None:
    passed = build_validation_outcome(verdict="PASS", check_id="ok", evaluated_at=NOW)
    assert parse_validation_outcome(passed) == passed
    assert validate_reason_code("RISK.LIMIT") == "RISK.LIMIT"
    assert get_severity_rank("CRITICAL") == 3
    with pytest.raises(ValidationError):
        validate_reason_code("bad")
    with pytest.raises(ValidationError):
        get_severity_rank("BAD")
    with pytest.raises(ValidationError):
        build_validation_outcome(verdict="BLOCK", check_id="x", evaluated_at=NOW)


def test_idempotency_all_verdicts_and_failures() -> None:
    key = derive_idempotency_key(owner="trading:orders", intent={"order": "1"})
    assert parse_idempotency_key(key) == key
    assert get_key_owner(key) == "trading:orders"
    assert (
        evaluate_reservation(
            key=key, owner="trading:orders", prior_reservation=None, observed_at=NOW
        )["verdict"]
        == "NEW"
    )
    expired = build_reservation(key=key, reserved_at=NOW, ttl_seconds=1)
    assert is_reservation_expired(expired, observed_at=NOW + timedelta(seconds=1))
    assert (
        evaluate_reservation(
            key=key,
            owner="trading:orders",
            prior_reservation=expired,
            observed_at=NOW + timedelta(seconds=2),
        )["verdict"]
        == "EXPIRED"
    )
    completed = build_reservation(
        key=key,
        reserved_at=NOW,
        ttl_seconds=30,
        state="COMPLETED",
        prior_result={"fill": "1"},
    )
    assert (
        evaluate_reservation(
            key=key,
            owner="trading:orders",
            prior_reservation=completed,
            observed_at=NOW,
        )["verdict"]
        == "DUPLICATE_COMPLETED"
    )
    with pytest.raises(ValidationError):
        derive_idempotency_key(owner="bad", intent={"order": "1"})


def test_random_draws_and_failures() -> None:
    stream = derive_random_stream(3, "fills")
    uniform, stream = next_uniform(stream, lower="1", upper="2", decimal_places=4)
    integer, stream = next_int(stream, lower=1, upper=1)
    choice, stream = next_choice(stream, ["A", "B"], weights=[1, 2])
    assert Decimal(uniform) >= 1
    assert integer == 1
    assert choice in {"A", "B"}
    assert stream["draw_index"] == 3
    with pytest.raises(ValidationError):
        derive_random_stream(True, "x")
    with pytest.raises(ValidationError):
        next_uniform(stream, lower=2, upper=1)
    with pytest.raises(ValidationError):
        next_int(stream, lower=2, upper=1)
    with pytest.raises(ValidationError):
        next_choice(stream, [])


def test_remaining_fail_closed_branches() -> None:
    """Exercise malformed evidence branches needed for per-file coverage."""
    with pytest.raises(ValidationError):
        route_audit_event({}, lambda _: None)
    with pytest.raises(ValidationError):
        build_transition_record(
            entity_id="",
            source_state="A",
            target_state="B",
            outcome="ACCEPTED",
            reason_code="EDGE.DECLARED",
            actor_ref="user",
            occurred_at=NOW,
            sequence=1,
        )
    with pytest.raises(ValidationError):
        build_transition_table({}, terminal_states=[])
    with pytest.raises(ValidationError):
        build_transition_table(
            {"A": ["B"], "B": []}, terminal_states=["B"], ranks={"A": 0}
        )
    table = build_transition_table(
        {"A": ["B"], "B": ["C"], "C": []},
        terminal_states=["C"],
        ranks={"A": 0, "B": 1, "C": 2},
    )
    assert attempt_transition(table, "B", "A")["outcome"] == "REGRESSED"
    with pytest.raises(ValidationError):
        attempt_transition(table, "UNKNOWN", "C")
    value = build_exact_unit("2", kind="QUANTITY")
    with pytest.raises(ValidationError):
        quantize_exact(value, "1", direction="BAD")
    with pytest.raises(ValidationError):
        quantize_exact(value, 0.1, direction="DOWN")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        to_venue_local(NOW, "No/Such_Zone")
    with pytest.raises(ValidationError):
        parse_time_stamp({})
    with pytest.raises(ValidationError):
        from_venue_local("bad", "UTC")
    detailed = build_validation_outcome(
        verdict="WARN",
        check_id="x",
        evaluated_at=NOW,
        reason_codes=["DATA.STALE"],
        severity="WARNING",
        corrective_actions=["Refresh feed"],
        evidence_refs=[
            "record-1",
            build_profile_ref(
                profile_kind="risk", profile_id="p", version="1", content_hash="a" * 64
            ),
        ],
    )
    assert detailed["corrective_actions"] == ["Refresh feed"]
    with pytest.raises(ValidationError):
        build_validation_outcome(
            verdict="WARN",
            check_id="x",
            evaluated_at=NOW,
            reason_codes=["DATA.STALE"],
            corrective_actions=["api_token=secret"],
        )  # pragma: allowlist secret
    with pytest.raises(ValidationError):
        build_validation_outcome(
            verdict="WARN",
            check_id="x",
            evaluated_at=NOW,
            reason_codes=["DATA.STALE"],
            evidence_refs=[{}],
        )
    with pytest.raises(ValidationError):
        parse_validation_outcome({})
    key = derive_idempotency_key(owner="trading:orders", intent={"order": "1"})
    with pytest.raises(ValidationError):
        build_reservation(key=key, reserved_at=NOW, ttl_seconds=0)
    with pytest.raises(ValidationError):
        build_reservation(key=key, reserved_at=NOW, ttl_seconds=1, prior_result="bad")
    with pytest.raises(ValidationError):
        is_reservation_expired({}, observed_at=NOW)
    with pytest.raises(ValidationError):
        evaluate_reservation(
            key=key, owner="data:jobs", prior_reservation=None, observed_at=NOW
        )
    malformed = build_reservation(key=key, reserved_at=NOW, ttl_seconds=30)
    malformed["state"] = "BAD"
    with pytest.raises(ValidationError):
        evaluate_reservation(
            key=key,
            owner="trading:orders",
            prior_reservation=malformed,
            observed_at=NOW,
        )
    definition = ErrorDefinition(
        code="DOMAIN_FAILURE",
        domain="utils",
        description="Failure",
        category="legacy",
        severity="error",
        retryable=False,
        operator_action="Inspect",
    )
    with pytest.raises(ValidationError):
        validate_error_catalog({"DOMAIN_FAILURE": definition})
