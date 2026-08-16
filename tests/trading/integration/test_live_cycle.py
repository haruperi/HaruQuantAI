"""Workflow integration for the public-domain live evaluation cycle."""

# ruff: noqa: ARG005
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import pytest
from app.services.trading import (
    create_live_session,
    create_readiness_assessment,
    run_live_evaluation_cycle,
    start_live_session,
)

from tests.trading.conftest import (
    NOW,
    CountingAdapter,
    action_policy,
    auth_context,
    broker_connection,
    evaluation_dependencies,
    evaluation_evidence,
    evaluation_risk_decision,
    inactive_kill_switch_hierarchy,
    symbol_capability,
    trade_intent,
)


@pytest.mark.anyio
async def test_cycle_submits_intent_and_never_sizes() -> None:
    """Run the complete demo cycle with the exact Risk-approved size."""
    deps, calls = evaluation_dependencies(trade_intent())
    adapter = CountingAdapter()
    connection = broker_connection()
    audits: list[object] = []

    async def passed() -> bool:
        """Return successful lifecycle reconciliation evidence."""
        return True

    session = create_live_session(
        store=deps.store,
        connection=connection,
        broker_adapter=cast("object", adapter),
        feature_flags=SimpleNamespace(broker_id="mt5", environment="demo"),
        risk_decision_source=lambda request: evaluation_risk_decision(),
        action_policy_source=lambda request: action_policy(request.action),
        kill_switch_source=inactive_kill_switch_hierarchy,
        readiness_source=lambda request, supplied_evidence: create_readiness_assessment(
            passed=True,
            failed_check_codes=(),
            evidence_refs={"data_authority_id": "data-001"},
            assessed_at=NOW,
        ),
        adapter_capability_source=lambda request: symbol_capability(
            request.route,
            request.provider_id,
            request.symbol,
        )[0],
        auth_context_source=auth_context,
        pre_audit_sink=audits.append,
        event_sink=lambda event: None,
        startup_reconcile=passed,
        drain_in_flight=passed,
        flush_evidence=passed,
        shutdown_reconcile=passed,
        clock=lambda: NOW,
    )
    await start_live_session(
        session,
        {
            "RUNTIME_PROFILE": "demo",
            "EXECUTION_ROUTE": "demo",
            "ALLOW_LIVE_MUTATIONS": False,
            "LIVE_WORKFLOW_TIMEOUT_SECONDS": "10",
            "SHUTDOWN_BUDGET_SECONDS": "5",
            "IDEMPOTENCY_RETENTION_SECONDS": 600,
            "CONCURRENCY_LOCK_TIMEOUT_SECONDS": "30",
            "MAX_STALENESS_SECONDS": {
                "route_snapshot": "30",
                "risk_decision": "30",
                "kill_switch": "30",
            },
            "DATA_AUTHORITY_ID": "data-001",
        },
        {
            "data_authority_id": "data-001",
            "adapter_security_profile": "approved",
            "startup_evidence_fresh": True,
        },
    )
    deps = replace(
        deps,
        connection=connection,
        broker_adapter=cast("object", adapter),
        live_session=session,
    )

    outcome = await run_live_evaluation_cycle(deps, evaluation_evidence())

    assert outcome.status == "success"
    assert outcome.metadata.extensions["legacy_status"] == "sent"
    assert calls == [
        "data.market",
        "data.account",
        "data.market_context",
        "indicators",
        "strategy",
        "risk",
    ]
    assert adapter.calls == 1
    assert adapter.request is not None
    assert adapter.request.quantity == Decimal("0.50")
    assert len(audits) == 1
    assert deps.store.load_projection(("demo", "account-001", "mt5")) is not None
