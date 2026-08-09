"""FEAT-BRK-16: exercise health-aware primary/backup route discipline.

This standalone usage program drives every public operation of the
``route_discipline`` feature (``TC-IMP-BRK-09``) through the documented public
API using bounded, secret-safe, deterministic data. It builds and parses a
``RoutePlan v1`` and ``FailoverDecision v1`` contract and proves the
fail-closed policy that no write is silently rerouted across brokers.
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from app.services.brokers import (
    build_broker_failover_decision,
    build_broker_route_plan,
    parse_broker_failover_decision,
    parse_broker_route_plan,
)
from app.services.brokers.contracts.enums import BrokerEnvironment, BrokerId

_OBSERVED_AT = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)


def _feature_header(title: str) -> None:
    """Print feature title and module-flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


def fr_brokers_136_route_plan() -> None:
    """FR-BRK-136: build and parse a health-aware RoutePlan v1."""
    _header("FR-BRK-136: Health-Aware Route Plan (build/parse)")
    plan = build_broker_route_plan(
        plan_id="plan-cockpit-1",
        primary_broker=BrokerId.MT5,
        primary_environment=BrokerEnvironment.DEMO,
        primary_readiness="READY",
        backup_broker=BrokerId.CTRADER,
        backup_environment=BrokerEnvironment.DEMO,
        backup_readiness="DEGRADED",
        selected_route=BrokerId.MT5.value,
        route_state="READY",
        write_failover_policy="RECOVERY_ONLY",
        created_at=_OBSERVED_AT,
    )
    parsed = parse_broker_route_plan(plan)
    print(f"Success -> route plan {parsed['plan_id']} parsed")
    print(
        f"Data -> schema_id={parsed['schema_id']} "
        f"primary={parsed['primary_broker']} selected={parsed['selected_route']} "
        f"policy={parsed['write_failover_policy']}"
    )


def fr_brokers_137_failover_decision() -> None:
    """FR-BRK-137: build and parse a fail-closed FailoverDecision v1."""
    _header("FR-BRK-137: Failover Decision (build/parse, fail-closed)")
    decision = build_broker_failover_decision(
        decision_id="dec-cockpit-1",
        plan_id="plan-cockpit-1",
        decision="FAILOVER_READ_ONLY",
        active_broker=BrokerId.CTRADER,
        active_environment=BrokerEnvironment.DEMO,
        write_permitted=False,
        read_permitted=True,
        reason="primary_degraded",
        decided_at=_OBSERVED_AT + timedelta(seconds=1),
    )
    parsed = parse_broker_failover_decision(decision)
    print(f"Success -> failover decision {parsed['decision_id']} parsed")
    print(
        f"Data -> schema_id={parsed['schema_id']} decision={parsed['decision']} "
        f"write_permitted={parsed['write_permitted']} active={parsed['active_broker']}"
    )


def fr_brokers_138_no_silent_write_reroute() -> None:
    """FR-BRK-138: prove writes are never silently rerouted across brokers."""
    _header("FR-BRK-138: No Silent Cross-Broker Write Reroute (fail-closed)")
    try:
        build_broker_failover_decision(
            decision_id="dec-blocked",
            plan_id="plan-cockpit-1",
            decision="FAILOVER_READ_ONLY",
            active_broker=BrokerId.CTRADER,
            active_environment=BrokerEnvironment.DEMO,
            write_permitted=True,
            read_permitted=True,
            reason="primary_degraded",
            decided_at=_OBSERVED_AT,
        )
    except Exception as error:  # noqa: BLE001
        print("Success -> write reroute blocked fail-closed")
        print(f"Data -> blocked={type(error).__name__}: {error}")
        return
    raise SystemExit("write reroute was not blocked")


def _run() -> None:
    """Exercise the route-discipline feature through the public API."""
    _feature_header(
        "FEATURE: FEAT-BRK-16 — route_discipline/ — "
        "Health-Aware Primary/Backup Route Discipline\n\n"
        "Purpose: Fail-closed health-aware routing with no duplicate order "
        "submission and no silent cross-broker write rerouting.\n\n"
        "Module flow:\n"
        "-> build/parse route plan\n"
        "-> build/parse failover decision\n"
        "-> prove no silent write reroute"
    )
    fr_brokers_136_route_plan()
    fr_brokers_137_failover_decision()
    fr_brokers_138_no_silent_write_reroute()


def main() -> None:
    """Run the standalone route-discipline usage program."""
    _run()


if __name__ == "__main__":
    main()
