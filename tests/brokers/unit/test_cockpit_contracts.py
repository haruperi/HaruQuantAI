"""Trading Cockpit Phase 0 contract-transport unit tests.

Covers the versioned cross-domain contract build/parse pairs added by
``TC-IMP-BRK-01`` (InstrumentVenueProfile), ``TC-IMP-BRK-03`` (BrokerHealth),
``TC-IMP-BRK-04`` (BrokerAccountSnapshot), ``TC-IMP-BRK-07`` (UNKNOWN result),
``TC-IMP-BRK-08`` (BrokerReconciliationSnapshot), and ``TC-IMP-BRK-09``
(RoutePlan / FailoverDecision). Each test exercises the build/parse round-trip,
integrity-hash tamper detection, version-incompatibility rejection, and the
fail-closed policy that the cockpit safety boundary requires.
"""

from datetime import UTC, datetime, timedelta

import pytest
from app.services.brokers import (
    build_broker_account_snapshot,
    build_broker_failover_decision,
    build_broker_health,
    build_broker_reconciliation_snapshot,
    build_broker_route_plan,
    build_broker_unknown_result,
    build_instrument_venue_profile,
    enforce_no_blind_resubmission,
    is_broker_unknown_result,
    parse_broker_account_snapshot,
    parse_broker_failover_decision,
    parse_broker_health,
    parse_broker_reconciliation_snapshot,
    parse_broker_route_plan,
    parse_instrument_venue_profile,
)
from app.services.brokers.contracts.enums import (
    BrokerEnvironment,
    BrokerId,
    BrokerResubmissionPolicy,
)
from app.utils.errors.exceptions import ValidationError

_NOW = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)


# --- TC-IMP-BRK-01: InstrumentVenueProfile v1 ---


def _profile_kwargs() -> dict[str, object]:
    return {
        "broker": BrokerId.MT5,
        "provider_symbol": "EURUSD",
        "canonical_symbol": "EUR/USD",
        "asset_class": "FX",
        "venue": "mt5-demo",
        "tick_size": "0.00001",
        "price_precision": 5,
        "quantity_step": "0.01",
        "contract_multiplier": "100000",
        "currency": "USD",
        "session_calendar": {"mon_open": "00:00"},
        "order_types": ("MARKET", "LIMIT"),
        "time_in_force": ("GTC", "DAY"),
        "margin_eligible": True,
        "shortable": False,
        "settlement": "T+2",
        "halt_state": "OPEN",
        "lifecycle_eligibility": "TRADEABLE",
        "source_timestamp": _NOW,
    }


def test_instrument_venue_profile_round_trip_preserves_evidence() -> None:
    """Build then parse yields a stable, equal profile mapping."""
    profile = build_instrument_venue_profile(**_profile_kwargs())
    parsed = parse_instrument_venue_profile(profile)
    assert parsed["contract_version"] == "v1"
    assert parsed["schema_id"] == "brokers.instrument_venue_profile.v1"
    assert parsed["broker"] == "mt5"
    # JSON-safe transport canonicalizes tuples to lists.
    assert list(parsed["order_types"]) == ["MARKET", "LIMIT"]
    assert parsed["integrity_hash"] == profile["integrity_hash"]


def test_instrument_venue_profile_tamper_detection() -> None:
    """A mutated field breaks the integrity hash."""
    profile = build_instrument_venue_profile(**_profile_kwargs())
    tampered = dict(profile)
    tampered["tick_size"] = "0.001"
    with pytest.raises(ValidationError):
        parse_instrument_venue_profile(tampered)


def test_instrument_venue_profile_rejects_unknown_asset_class() -> None:
    """An undeclared asset class is rejected, not defaulted."""
    kwargs = _profile_kwargs()
    kwargs["asset_class"] = "DERIVATIVE"
    with pytest.raises(ValidationError):
        build_instrument_venue_profile(**kwargs)


# --- TC-IMP-BRK-03: BrokerHealth v1 ---


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


# --- TC-IMP-BRK-04: BrokerAccountSnapshot v1 (distinct Brokers name) ---


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

    import app.services.brokers.contracts.account_snapshot as module

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


# --- TC-IMP-BRK-07: UNKNOWN result + blind-resubmission prohibition ---


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


# --- TC-IMP-BRK-08: BrokerReconciliationSnapshot v1 ---


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


# --- TC-IMP-BRK-09: RoutePlan / FailoverDecision ---


def test_route_plan_round_trip() -> None:
    """Build then parse yields a stable route plan."""
    plan = build_broker_route_plan(
        plan_id="plan-1",
        primary_broker=BrokerId.MT5,
        primary_environment=BrokerEnvironment.DEMO,
        primary_readiness="READY",
        backup_broker=BrokerId.CTRADER,
        backup_environment=BrokerEnvironment.DEMO,
        backup_readiness="DEGRADED",
        selected_route="mt5",
        route_state="READY",
        write_failover_policy="RECOVERY_ONLY",
        created_at=_NOW,
    )
    parsed = parse_broker_route_plan(plan)
    assert parsed["selected_route"] == "mt5"
    assert parsed["schema_id"] == "brokers.route_plan.v1"


def test_route_plan_fail_closed_when_no_ready_route() -> None:
    """A non-ready primary with no backup cannot report a ready aggregate."""
    with pytest.raises(ValidationError):
        build_broker_route_plan(
            plan_id="plan-2",
            primary_broker=BrokerId.MT5,
            primary_environment=BrokerEnvironment.DEMO,
            primary_readiness="UNAVAILABLE",
            backup_broker=None,
            backup_environment=None,
            backup_readiness=None,
            selected_route=None,
            route_state="READY",
            write_failover_policy="NEVER",
            created_at=_NOW,
        )


def test_failover_decision_round_trip() -> None:
    """Build then parse yields a stable failover decision."""
    decision = build_broker_failover_decision(
        decision_id="dec-1",
        plan_id="plan-1",
        decision="HOLD_PRIMARY",
        active_broker=BrokerId.MT5,
        active_environment=BrokerEnvironment.DEMO,
        write_permitted=True,
        read_permitted=True,
        reason="primary_healthy",
        decided_at=_NOW,
    )
    parsed = parse_broker_failover_decision(decision)
    assert parsed["decision"] == "HOLD_PRIMARY"
    assert parsed["schema_id"] == "brokers.failover_decision.v1"


def test_failover_decision_blocks_writes_on_failover() -> None:
    """A read-only failover never permits writes (no silent cross-broker write)."""
    with pytest.raises(ValidationError):
        build_broker_failover_decision(
            decision_id="dec-2",
            plan_id="plan-1",
            decision="FAILOVER_READ_ONLY",
            active_broker=BrokerId.CTRADER,
            active_environment=BrokerEnvironment.DEMO,
            write_permitted=True,
            read_permitted=True,
            reason="primary_degraded",
            decided_at=_NOW,
        )


def test_failover_decision_block_permits_neither() -> None:
    """A BLOCK decision permits neither reads nor writes."""
    with pytest.raises(ValidationError):
        build_broker_failover_decision(
            decision_id="dec-3",
            plan_id="plan-1",
            decision="BLOCK",
            active_broker=None,
            active_environment=None,
            write_permitted=False,
            read_permitted=True,
            reason="no_route",
            decided_at=_NOW,
        )
