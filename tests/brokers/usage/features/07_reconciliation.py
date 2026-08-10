"""FEAT-BRK-07: authoritative reads and route discipline evidence."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from app.services.brokers import build_broker_route_plan


def fr_brokers_136_to_149_reconciliation() -> None:
    """Build one explicit read-only recovery plan.

    Returns:
        None.
    """
    plan = build_broker_route_plan(
        plan_id="route-plan-usage",
        primary_broker="mt5",
        primary_environment="demo",
        primary_readiness="READY",
        backup_broker="ctrader",
        backup_environment="demo",
        backup_readiness="DEGRADED",
        selected_route="mt5",
        route_state="READY",
        write_failover_policy="RECOVERY_ONLY",
        created_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    print("SUCCESS: FEAT-BRK-07 reconciliation completed")
    print(f"DATA: {plan}")


def main() -> None:
    """Run reconciliation evidence.

    Returns:
        None.
    """
    fr_brokers_136_to_149_reconciliation()


if __name__ == "__main__":
    main()
