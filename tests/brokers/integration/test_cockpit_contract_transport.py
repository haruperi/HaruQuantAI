"""Producer-consumer contract-transport compatibility tests.

Every new versioned cross-domain contract added by the Trading Cockpit Phase 0
reconciliation must round-trip through its ``build_*``/``parse_*`` pair and
survive a JSON serialization boundary, so a consumer in another process can
parse what the Brokers producer built. This is the binding CONTRACT gate.
"""

import json
from datetime import UTC, datetime, timedelta

import pytest
from app.services.brokers import (
    build_broker_account_snapshot,
    build_broker_failover_decision,
    build_broker_health,
    build_broker_reconciliation_snapshot,
    build_broker_route_plan,
    build_instrument_venue_profile,
    parse_broker_account_snapshot,
    parse_broker_failover_decision,
    parse_broker_health,
    parse_broker_reconciliation_snapshot,
    parse_broker_route_plan,
    parse_instrument_venue_profile,
)
from app.utils.errors.exceptions import ValidationError

_NOW = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)


def _round_trip_through_json(mapping: dict[str, object]) -> dict[str, object]:
    """Serialize and deserialize a mapping through a JSON boundary.

    Args:
        mapping: Candidate JSON-safe mapping.

    Returns:
        The deserialized mapping.
    """
    return json.loads(json.dumps(mapping))


def test_instrument_venue_profile_survives_json_transport() -> None:
    """InstrumentVenueProfile v1 round-trips through JSON."""
    profile = build_instrument_venue_profile(
        broker="mt5",
        provider_symbol="EURUSD",
        canonical_symbol="EUR/USD",
        asset_class="FX",
        venue="mt5-demo",
        tick_size="0.00001",
        price_precision=5,
        quantity_step="0.01",
        contract_multiplier="100000",
        currency="USD",
        session_calendar={"mon_open": "00:00"},
        order_types=("MARKET", "LIMIT"),
        time_in_force=("GTC", "DAY"),
        margin_eligible=True,
        shortable=False,
        settlement="T+2",
        halt_state="OPEN",
        lifecycle_eligibility="TRADEABLE",
        source_timestamp=_NOW,
    )
    parsed = parse_instrument_venue_profile(_round_trip_through_json(profile))
    assert parsed["contract_version"] == "v1"
    assert parsed["integrity_hash"] == profile["integrity_hash"]


def test_broker_health_survives_json_transport() -> None:
    """BrokerHealth v1 round-trips through JSON."""
    health = build_broker_health(
        broker="mt5",
        environment="demo",
        observed_at=_NOW,
        freshness_budget_sec=5.0,
        as_of=_NOW,
        authentication_state="AUTHENTICATED",
        session_state="READY",
        api_heartbeat="ALIVE",
        stream_heartbeat="ALIVE",
        round_trip_latency_ms=42.0,
        error_rate=0.0,
        in_maintenance=False,
        route_readiness="READY",
        qualifying_failure_count=0,
    )
    parsed = parse_broker_health(_round_trip_through_json(health))
    assert parsed["route_readiness"] == "READY"


def test_broker_health_stale_sample_survives_json_transport() -> None:
    """A fail-closed stale BrokerHealth round-trips through JSON."""
    health = build_broker_health(
        broker="mt5",
        environment="demo",
        observed_at=_NOW,
        freshness_budget_sec=1.0,
        as_of=_NOW + timedelta(seconds=5),
        authentication_state="AUTHENTICATED",
        session_state="READY",
        api_heartbeat="ALIVE",
        stream_heartbeat="ALIVE",
        round_trip_latency_ms=42.0,
        error_rate=0.0,
        in_maintenance=False,
        route_readiness="READY",
        qualifying_failure_count=0,
    )
    assert health["route_readiness"] == "STALE"
    parsed = parse_broker_health(_round_trip_through_json(health))
    assert parsed["route_readiness"] == "STALE"


def test_broker_account_snapshot_survives_json_transport() -> None:
    """BrokerAccountSnapshot v1 round-trips through JSON."""
    snapshot = build_broker_account_snapshot(
        broker="mt5",
        environment="demo",
        account_reference="acc-1",
        currency="USD",
        balance="10000",
        equity="10050",
        margin_used="200",
        margin_free="9850",
        margin_level="5025.00",
        leverage="1:100",
        permissions="FULL",
        source_timestamp=_NOW,
    )
    parsed = parse_broker_account_snapshot(_round_trip_through_json(snapshot))
    assert parsed["balance"] == "10000"


def test_broker_account_snapshot_optional_fields_survive_json_transport() -> None:
    """Optional account fields survive JSON transport as null."""
    snapshot = build_broker_account_snapshot(
        broker="yahoo",
        environment="sandbox",
        account_reference=None,
        currency="USD",
        balance="0",
        equity="0",
        margin_used=None,
        margin_free=None,
        margin_level=None,
        leverage=None,
        permissions="UNKNOWN",
        source_timestamp=_NOW,
    )
    parsed = parse_broker_account_snapshot(_round_trip_through_json(snapshot))
    assert parsed["account_reference"] is None
    assert parsed["leverage"] is None
    assert parsed["margin_used"] is None


def test_broker_reconciliation_snapshot_survives_json_transport() -> None:
    """BrokerReconciliationSnapshot v1 round-trips through JSON."""
    snapshot = build_broker_reconciliation_snapshot(
        broker="mt5",
        environment="demo",
        account_reference="acc-1",
        as_of=_NOW,
        venue_state="OPEN",
        open_orders_state="COMPLETE",
        open_orders=({"order_id": "o1"},),
        fills_state="PARTIAL",
        fills=({"deal_id": "d1"},),
        positions_state="UNKNOWN",
        positions=(),
        balances_state="UNAVAILABLE",
        balances=(),
    )
    parsed = parse_broker_reconciliation_snapshot(_round_trip_through_json(snapshot))
    assert parsed["fills_state"] == "PARTIAL"


def test_route_plan_survives_json_transport() -> None:
    """RoutePlan v1 round-trips through JSON."""
    plan = build_broker_route_plan(
        plan_id="plan-1",
        primary_broker="mt5",
        primary_environment="demo",
        primary_readiness="READY",
        backup_broker="ctrader",
        backup_environment="demo",
        backup_readiness="DEGRADED",
        selected_route="mt5",
        route_state="READY",
        write_failover_policy="RECOVERY_ONLY",
        created_at=_NOW,
    )
    parsed = parse_broker_route_plan(_round_trip_through_json(plan))
    assert parsed["selected_route"] == "mt5"


def test_failover_decision_survives_json_transport() -> None:
    """FailoverDecision v1 round-trips through JSON."""
    decision = build_broker_failover_decision(
        decision_id="dec-1",
        plan_id="plan-1",
        decision="FAILOVER_RECOVERY",
        active_broker="ctrader",
        active_environment="demo",
        write_permitted=False,
        read_permitted=True,
        reason="primary_unhealthy",
        decided_at=_NOW,
    )
    parsed = parse_broker_failover_decision(_round_trip_through_json(decision))
    assert parsed["decision"] == "FAILOVER_RECOVERY"
    assert parsed["write_permitted"] is False


def test_unknown_contract_version_is_rejected() -> None:
    """A contract with an incompatible version is rejected by every parser."""
    health = build_broker_health(
        broker="mt5",
        environment="demo",
        observed_at=_NOW,
        freshness_budget_sec=5.0,
        as_of=_NOW,
        authentication_state="AUTHENTICATED",
        session_state="READY",
        api_heartbeat="ALIVE",
        stream_heartbeat="ALIVE",
        round_trip_latency_ms=42.0,
        error_rate=0.0,
        in_maintenance=False,
        route_readiness="READY",
        qualifying_failure_count=0,
    )
    tampered = dict(health)
    tampered["contract_version"] = "v2"
    with pytest.raises(ValidationError):
        parse_broker_health(tampered)
