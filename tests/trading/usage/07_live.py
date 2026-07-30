"""Executable Trading live usage example.

Demonstrates LiveSession lifecycle and evaluate_live_gate.
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.brokers import build_broker_connection_config
from app.services.trading import (
    create_live_session,
    create_trading_request,
    evaluate_live_gate,
    get_live_session_status,
    get_trading_route,
    is_live_session_started,
    start_live_session,
    stop_live_session,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)


async def _passed() -> bool:
    """Return one successful usage lifecycle step."""
    return True


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _session() -> Any:
    """Build a package-only usage session."""
    connection = build_broker_connection_config(
        broker_id="mt5",
        environment="live",
        provider_enabled=True,
    )
    adapter = SimpleNamespace(contract_version="v1", schema_id="brokers.adapter.v1")
    flags = SimpleNamespace(
        broker_id="mt5",
        environment="live",
    )
    return create_live_session(
        store=object(),
        connection=connection,
        broker_adapter=adapter,
        feature_flags=flags,
        risk_decision_source=lambda _request: None,
        action_policy_source=lambda _request: None,
        kill_switch_source=lambda _request: (),
        readiness_source=lambda _req, _ev: None,
        adapter_capability_source=lambda _request: {},
        auth_context_source=lambda _request: None,
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
    print(f"Initial session started state: {is_live_session_started(session)}")

    # Start session
    start_res = await start_live_session(session, _config(), _evidence())
    print(f"Session start status: {start_res.status}, evidence: {start_res.data}")

    # Session status
    status_res = get_live_session_status(session)
    status_data = status_res.data
    assert status_data is not None
    print(f"LiveSession status health: {status_data['health']}")

    # Evaluate live gate
    request = create_trading_request(
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        route=get_trading_route("live"),
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
    stop_res = await stop_live_session(session)
    print(f"Session stop status: {stop_res.status}, evidence: {stop_res.data}")


def example_live() -> None:
    """Demonstrate Trading live session operations."""
    _header("Demonstrate Trading live session operations.")
    print("Trading Example 7: Live Session Lifecycle and Safety Gates")
    asyncio.run(_async_example())


def fr_trd_032() -> None:
    """FR-TRD-032: The system shall use one stateful lifecycle object for admission, startup evidence, recovery lock, in-flight work, and shutdown."""
    _header(
        "FR-TRD-032: The system shall use one stateful lifecycle object for admission, startup evidence, recovery lock, in-flight work, and shutdown."
    )
    example_live()


def fr_trd_033() -> None:
    """FR-TRD-033: The system shall validate config/security, bind opaque Data authority, and complete startup reconciliation before enabling mutation."""
    _header(
        "FR-TRD-033: The system shall validate config/security, bind opaque Data authority, and complete startup reconciliation before enabling mutation."
    )
    example_live()


def fr_trd_034() -> None:
    """FR-TRD-034: The system shall return the actual session mode, admission, authority, health, reconciliation, and unresolved-work state."""
    _header(
        "FR-TRD-034: The system shall return the actual session mode, admission, authority, health, reconciliation, and unresolved-work state."
    )
    example_live()


def fr_trd_035() -> None:
    """FR-TRD-035: The system shall stop admission, drain/mark work, flush evidence, reconcile, and report every incomplete shutdown step."""
    _header(
        "FR-TRD-035: The system shall stop admission, drain/mark work, flush evidence, reconcile, and report every incomplete shutdown step."
    )
    example_live()


def fr_trd_036() -> None:
    """FR-TRD-036: The system shall enforce the canonical mandatory gate order using typed authority sources owned by the injected session and prohibit passthrough Risk or caller-declared emergency authority. JSON evidence carries facts/references only."""
    _header(
        "FR-TRD-036: The system shall enforce the canonical mandatory gate order using typed authority sources owned by the injected session and prohibit passthrough Risk or caller-declared emergency authority. JSON evidence carries facts/references only."
    )
    example_live()


def main() -> None:
    """Run Trading live usage example."""
    example_live()


if __name__ == "__main__":
    main()
