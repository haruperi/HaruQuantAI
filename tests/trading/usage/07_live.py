"""Executable Trading live usage example.

Demonstrates LiveSession lifecycle and evaluate_live_gate.
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import cast

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers.contracts import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerFeatureFlags,
)
from app.services.trading.contracts import TradingRequest, TradingRoute
from app.services.trading.live import LiveSession, evaluate_live_gate
from app.services.trading.state import TradingStateStore

NOW = datetime(2026, 7, 19, tzinfo=UTC)


async def _passed() -> bool:
    """Return one successful usage lifecycle step."""
    return True


def _session() -> LiveSession:
    """Build a package-only usage session."""
    connection = cast(
        "BrokerConnectionConfig",
        SimpleNamespace(
            broker_id="test-broker",
            environment=BrokerEnvironment.LIVE,
            provider_enabled=True,
        ),
    )
    adapter = cast(
        "BrokerAdapter",
        SimpleNamespace(contract_version="v1", schema_id="brokers.adapter.v1"),
    )
    flags = cast(
        "BrokerFeatureFlags",
        SimpleNamespace(
            broker_id="test-broker",
            environment=BrokerEnvironment.LIVE,
        ),
    )
    return LiveSession(
        store=cast("TradingStateStore", object()),
        connection=connection,
        broker_adapter=adapter,
        feature_flags=flags,
        risk_decision_source=lambda _request: None,
        action_policy_source=lambda _request: None,
        kill_switch_source=lambda _request: (),
        readiness_source=lambda _req, _ev: cast("object", None),
        adapter_capability_source=lambda _request: {},
        pre_audit_sink=lambda _ev: None,
        event_sink=lambda _evt: None,
        startup_reconcile=_passed,
        drain_in_flight=_passed,
        flush_evidence=_passed,
        shutdown_reconcile=_passed,
        clock=lambda: NOW,
    )


def _config() -> dict[str, object]:
    """Return exact safe live usage config."""
    return {
        "RUNTIME_PROFILE": "live",
        "EXECUTION_ROUTE": "live",
        "ALLOW_LIVE_MUTATIONS": False,
        "LIVE_WORKFLOW_TIMEOUT_SECONDS": "30",
        "SHUTDOWN_BUDGET_SECONDS": "5",
        "IDEMPOTENCY_RETENTION_SECONDS": 600,
        "CONCURRENCY_LOCK_TIMEOUT_SECONDS": "30",
        "MAX_STALENESS_SECONDS": {
            "route_snapshot": "30",
            "risk_decision": "30",
            "kill_switch": "30",
        },
        "DATA_AUTHORITY_ID": "data-authority-001",
    }


def _evidence() -> dict[str, object]:
    """Return exact safe startup evidence."""
    return {
        "data_authority_id": "data-authority-001",
        "adapter_security_profile": "approved",
        "startup_evidence_fresh": True,
    }


async def _async_example() -> None:
    """Async portion of live session demonstration."""
    session = _session()
    print(f"Initial LiveSession started state: {session.started}")

    # Start session
    start_res = await session.start(_config(), _evidence())
    print(f"LiveSession start status: {start_res.status}")

    # Session status
    status_res = session.status()
    print(f"LiveSession status health: {status_res.data['health']}")

    # Evaluate live gate
    request = TradingRequest(
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
        route=TradingRoute.LIVE,
        action="submit_order",
        provider_id="test-broker",
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        intent_id="intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="lots",
        quantity=Decimal(1),
        risk_decision_id="risk-decision-001",
        action_policy_verdict_id="policy-verdict-001",
        approval_token_ref="token-001",
        idempotency_key="usage-idempotency-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )
    gate_res = await evaluate_live_gate(request, {}, session)
    print(f"Evaluated live gate result status: {gate_res.status}")

    # Stop session
    stop_res = await session.stop()
    print(f"LiveSession stop status: {stop_res.status}")


def example_live() -> None:
    """Demonstrate Trading live session operations."""
    print("=" * 80)
    print("Trading Example 7: Live Session Lifecycle and Safety Gates")
    print("=" * 80)
    asyncio.run(_async_example())


def main() -> None:
    """Run Trading live usage example."""
    example_live()


if __name__ == "__main__":
    main()
