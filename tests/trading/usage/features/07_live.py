"""Executable Trading live usage example.

Demonstrates FEAT-TRD-07 LiveSession lifecycle and evaluate_live_gate.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

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


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


async def _passed() -> bool:
    """Return one successful usage lifecycle step."""
    return True


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


def fr_trd_032() -> None:
    """FR-TRD-032: Stage 1 — Construct stateful LiveSession object for lifecycle governance."""
    _header("Stage 1: Session Construction - Create LiveSession (FR-TRD-032)")
    session = _session()
    started = is_live_session_started(session)
    print("Output Result -> bool : bool")
    print(f"Data -> is_started={started}")


def fr_trd_033() -> None:
    """FR-TRD-033: Stage 2 — Start live session, bind Data authority, and reconcile."""
    _header("Stage 2: Session Startup - Start Live Session (FR-TRD-033)")
    session = _session()
    start_res = asyncio.run(start_live_session(session, _config(), _evidence()))
    print(_format_result(start_res))
    print(f"Data -> status='{start_res.status}'")


def fr_trd_034() -> None:
    """FR-TRD-034: Stage 3 — Return session mode, admission, health, and reconciliation status."""
    _header("Stage 3: Session Status - Get Live Session Status (FR-TRD-034)")
    session = _session()
    asyncio.run(start_live_session(session, _config(), _evidence()))
    status_res = get_live_session_status(session)
    print(_format_result(status_res))
    print(f"Data -> status='{status_res.status}'")


def fr_trd_035() -> None:
    """FR-TRD-035: Stage 3 — Stop admission, drain work, flush evidence, and stop session."""
    _header("Stage 3: Session Shutdown - Stop Live Session (FR-TRD-035)")
    session = _session()
    asyncio.run(start_live_session(session, _config(), _evidence()))
    stop_res = asyncio.run(stop_live_session(session))
    print(_format_result(stop_res))
    print(f"Data -> status='{stop_res.status}'")


def fr_trd_036() -> None:
    """FR-TRD-036: Stage 2 — Evaluate live gate against mandatory gate order."""
    _header("Stage 2: Live Gate Evaluation - Evaluate Live Gate (FR-TRD-036)")
    session = _session()
    asyncio.run(start_live_session(session, _config(), _evidence()))
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
    gate_res = asyncio.run(evaluate_live_gate(request, {}, session))
    print(_format_result(gate_res))
    print(f"Data -> status='{gate_res.status}'")


def _emit_requirement_success(function: object) -> object:
    """Wrap one example so direct execution emits its success contract."""

    def wrapped() -> None:
        function()
        requirement = function.__name__.removeprefix("fr_trd_").replace("_", "-")
        print(f"SUCCESS: FR-TRD-{requirement}")

    return wrapped


for _example_name, _example_function in tuple(globals().items()):
    if _example_name.startswith("fr_trd_") and callable(_example_function):
        globals()[_example_name] = _emit_requirement_success(_example_function)


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-TRD-07 — live/ — Live and Paper Session Lifecycle\n\n"
        "Purpose: Manage LiveSession lifecycle state, validate startup evidence, evaluate multi-stage safety gates, and govern graceful shutdown.\n\n"
        "Module flow:\n"
        "-> Stage 1: LiveSession initialization and configuration parameter binding\n"
        "-> Stage 2: Session startup reconciliation, authority binding, and live gate evaluation\n"
        "-> Stage 3: Session health status reporting, admission draining, and graceful shutdown"
    )

    # Stage 1: Session construction
    fr_trd_032()

    # Stage 2: Startup reconciliation & Gate evaluation
    fr_trd_033()
    fr_trd_036()

    # Stage 3: Status reporting & Graceful shutdown
    fr_trd_034()
    fr_trd_035()


if __name__ == "__main__":
    main()
