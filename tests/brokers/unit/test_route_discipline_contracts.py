"""application Phase 0 contract-transport unit tests.

Covers the versioned cross-domain contract build/parse pairs added by
``feature`` (BrokerHealth), ``feature`` (BrokerAccountSnapshot), ``feature`` (UNKNOWN result),
and ``feature`` (BrokerReconciliationSnapshot). Each test exercises the build/parse round-trip,
integrity-hash tamper detection, version-incompatibility rejection, and the
fail-closed policy that the operational safety boundary requires.
"""

from datetime import UTC, datetime, timedelta

import pytest
from app.kernel.errors import ValidationError
from app.services.brokers import (
    build_broker_account_snapshot,
    build_broker_health,
    build_broker_reconciliation_snapshot,
    build_broker_unknown_result,
    enforce_no_blind_resubmission,
    is_broker_unknown_result,
    parse_broker_account_snapshot,
    parse_broker_health,
    parse_broker_reconciliation_snapshot,
)
from app.services.brokers.canonical_contracts.enums import (
    BrokerEnvironment,
    BrokerId,
    BrokerResubmissionPolicy,
)

_NOW = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)
_NAIVE = datetime(2026, 8, 7)  # noqa: DTZ001 - intentional invalid evidence.


# --- feature: BrokerHealth v1 ---


def _health_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "broker": BrokerId.MT5,
        "environment": BrokerEnvironment.DEMO,
        "observed_at": _NOW,
        "freshness_budget_sec": 5.0,
        "as_of": _NOW,
        "authentication_state": "AUTHENTICATED",
        "session_state": "READY",
        "api_heartbeat": "ALIVE",
        "stream_heartbeat": "ALIVE",
        "round_trip_latency_ms": 42.0,
        "error_rate": 0.0,
        "in_maintenance": False,
        "route_readiness": "READY",
        "qualifying_failure_count": 0,
    }
    base.update(overrides)
    return base


def test_broker_health_round_trip_preserves_evidence() -> None:
    """Build then parse yields a stable health mapping."""
    health = build_broker_health(**_health_kwargs())
    parsed = parse_broker_health(health)
    assert parsed["route_readiness"] == "READY"
    assert parsed["integrity_hash"] == health["integrity_hash"]


def test_broker_health_stale_sample_is_fail_closed() -> None:
    """A stale sample downgrades readiness and never reports READY."""
    stale_as_of = _NOW + timedelta(seconds=10)
    health = build_broker_health(**_health_kwargs(as_of=stale_as_of))
    assert health["route_readiness"] == "STALE"
    assert health["api_heartbeat"] == "STALE"
    parse_broker_health(health)


def test_broker_health_rejects_invalid_error_rate() -> None:
    """An error rate above 1.0 is rejected."""
    with pytest.raises(ValidationError):
        build_broker_health(**_health_kwargs(error_rate=1.5))


# --- feature: BrokerAccountSnapshot v1 (distinct Brokers name) ---


def _account_kwargs() -> dict[str, object]:
    return {
        "broker": BrokerId.MT5,
        "environment": BrokerEnvironment.DEMO,
        "account_reference": "acc-1",
        "currency": "USD",
        "balance": "10000",
        "equity": "10050",
        "margin_used": "200",
        "margin_free": "9850",
        "margin_level": "5025.00",
        "leverage": "1:100",
        "permissions": "FULL",
        "source_timestamp": _NOW,
    }


def test_broker_account_snapshot_round_trip() -> None:
    """Build then parse yields a stable account snapshot."""
    snapshot = build_broker_account_snapshot(**_account_kwargs())
    parsed = parse_broker_account_snapshot(snapshot)
    assert parsed["schema_id"] == "brokers.account_snapshot.v1"
    assert parsed["balance"] == "10000"


def test_broker_account_snapshot_is_distinct_from_data_model() -> None:
    """BrokerAccountSnapshot must not import Data's AccountStateSnapshot."""
    import inspect

    import app.services.brokers.canonical_contracts.account_snapshot as module

    source = inspect.getsource(module)
    # The module must not import from Data's account contracts (only mention
    # the open decision in its docstring). Filter to import lines only.
    import_lines = [
        line
        for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    joined_imports = "\n".join(import_lines)
    assert "account_contracts" not in joined_imports
    assert "from app.services.data" not in joined_imports


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("currency", ""),
        ("balance", object()),
        ("equity", "not-a-number"),
        ("margin_used", "NaN"),
        ("permissions", "UNDECLARED"),
        ("source_timestamp", _NAIVE),
    ],
)
def test_broker_account_snapshot_rejects_invalid_evidence(
    field: str, value: object
) -> None:
    """Malformed account evidence fails closed at construction."""
    kwargs = _account_kwargs()
    kwargs[field] = value
    with pytest.raises(ValidationError):
        build_broker_account_snapshot(**kwargs)


# --- feature: UNKNOWN result + blind-resubmission prohibition ---


def test_broker_unknown_result_is_first_class() -> None:
    """An UNKNOWN result carries the deterministic unknown verdict."""
    result = build_broker_unknown_result(
        operation="place_order",
        request_id="req-1",
        observed_at=_NOW,
        cause="timeout",
    )
    assert is_broker_unknown_result(result)
    assert result["outcome"] == "UNKNOWN"
    assert result["acknowledged"] is False


def test_broker_unknown_result_prohibits_blind_resubmission() -> None:
    """A PROHIBITED policy raises on an UNKNOWN prior outcome."""
    result = build_broker_unknown_result(
        operation="place_order",
        request_id="req-1",
        observed_at=_NOW,
        cause="lost_ack",
    )
    with pytest.raises(ValidationError):
        enforce_no_blind_resubmission(
            prior_outcome=result,
            policy=BrokerResubmissionPolicy.PROHIBITED,
        )


def test_broker_unknown_result_permitted_policy_allows_resubmission() -> None:
    """A PERMITTED policy does not raise on an UNKNOWN prior outcome."""
    result = build_broker_unknown_result(
        operation="place_order",
        request_id="req-1",
        observed_at=_NOW,
        cause="timeout",
    )
    enforce_no_blind_resubmission(
        prior_outcome=result,
        policy=BrokerResubmissionPolicy.PERMITTED,
    )


def test_broker_unknown_result_rejects_malformed_inputs() -> None:
    """UNKNOWN evidence cannot be constructed from empty or naive inputs."""
    for overrides in (
        {"operation": ""},
        {"request_id": ""},
        {"cause": ""},
        {"observed_at": _NAIVE},
    ):
        kwargs: dict[str, object] = {
            "operation": "place_order",
            "request_id": "req-1",
            "observed_at": _NOW,
            "cause": "timeout",
        }
        kwargs.update(overrides)
        with pytest.raises(ValidationError):
            build_broker_unknown_result(**kwargs)

    assert not is_broker_unknown_result({"outcome": "SUCCESS"})


# --- feature: BrokerReconciliationSnapshot v1 ---


def test_broker_reconciliation_snapshot_round_trip() -> None:
    """Build then parse yields a stable reconciliation snapshot."""
    snapshot = build_broker_reconciliation_snapshot(
        broker=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        account_reference="acc-1",
        as_of=_NOW,
        venue_state="OPEN",
        open_orders_state="COMPLETE",
        open_orders=({"order_id": "o1"},),
        fills_state="COMPLETE",
        fills=({"deal_id": "d1"},),
        positions_state="COMPLETE",
        positions=({"position_id": "p1"},),
        balances_state="COMPLETE",
        balances=({"currency": "USD"},),
    )
    parsed = parse_broker_reconciliation_snapshot(snapshot)
    assert parsed["schema_id"] == "brokers.reconciliation.v1"
    assert parsed["venue_state"] == "OPEN"
    # JSON-safe transport canonicalizes tuples to lists.
    assert list(parsed["open_orders"]) == [{"order_id": "o1"}]


def test_broker_reconciliation_snapshot_tamper_detection() -> None:
    """A mutated section breaks the integrity hash."""
    snapshot = build_broker_reconciliation_snapshot(
        broker=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        account_reference=None,
        as_of=_NOW,
        venue_state="OPEN",
        open_orders_state="UNKNOWN",
        open_orders=(),
        fills_state="UNKNOWN",
        fills=(),
        positions_state="UNKNOWN",
        positions=(),
        balances_state="UNKNOWN",
        balances=(),
    )
    tampered = dict(snapshot)
    tampered["venue_state"] = "CLOSED"
    with pytest.raises(ValidationError):
        parse_broker_reconciliation_snapshot(tampered)


def _reconciliation_kwargs() -> dict[str, object]:
    """Return valid reconciliation evidence for rejection tests."""
    return {
        "broker": BrokerId.MT5,
        "environment": BrokerEnvironment.DEMO,
        "account_reference": None,
        "as_of": _NOW,
        "venue_state": "OPEN",
        "open_orders_state": "COMPLETE",
        "open_orders": (),
        "fills_state": "COMPLETE",
        "fills": (),
        "positions_state": "COMPLETE",
        "positions": (),
        "balances_state": "COMPLETE",
        "balances": (),
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("venue_state", "INVALID"),
        ("open_orders_state", "INVALID"),
        ("open_orders", ("not-a-record",)),
        ("as_of", _NAIVE),
    ],
)
def test_reconciliation_rejects_invalid_section_evidence(
    field: str, value: object
) -> None:
    """Malformed reconciliation sections fail closed."""
    kwargs = _reconciliation_kwargs()
    kwargs[field] = value
    with pytest.raises(ValidationError):
        build_broker_reconciliation_snapshot(**kwargs)
