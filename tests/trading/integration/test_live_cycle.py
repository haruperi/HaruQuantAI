"""Workflow integration for the public-domain live evaluation cycle."""

# ruff: noqa: ARG005, INP001

from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import pytest
from app.services.brokers import (
    BrokerAdapter,
    BrokerFeatureFlags,
)
from app.services.trading.actions import run_live_evaluation_cycle
from app.services.trading.live import LiveSession
from app.services.trading.validation import ReadinessAssessment
from tests.trading.conftest import (
    NOW,
    CountingAdapter,
    action_policy,
    broker_connection,
    evaluation_dependencies,
    evaluation_evidence,
    evaluation_risk_decision,
    inactive_kill_switch,
    symbol_capability,
    trade_intent,
)


@pytest.mark.anyio
async def test_cycle_submits_intent_and_never_sizes() -> None:
    """Run the complete paper cycle with the exact Risk-approved size."""
    deps, calls = evaluation_dependencies(trade_intent())
    adapter = CountingAdapter()
    connection = broker_connection()
    audits: list[object] = []

    async def passed() -> bool:
        """Return successful lifecycle reconciliation evidence."""
        return True

    session = LiveSession(
        store=deps.store,
        connection=connection,
        broker_adapter=cast("BrokerAdapter", adapter),
        feature_flags=cast(
            "BrokerFeatureFlags",
            SimpleNamespace(
                broker_id=connection.broker_id,
                environment=connection.environment,
            ),
        ),
        risk_decision_source=lambda request: evaluation_risk_decision(),
        action_policy_source=lambda request: action_policy(request.action),
        kill_switch_source=lambda request: (inactive_kill_switch(),),
        readiness_source=lambda request, supplied_evidence: ReadinessAssessment(
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
        pre_audit_sink=audits.append,
        event_sink=lambda event: None,
        startup_reconcile=passed,
        drain_in_flight=passed,
        flush_evidence=passed,
        shutdown_reconcile=passed,
        clock=lambda: NOW,
    )
    await session.start(
        {
            "RUNTIME_PROFILE": "paper",
            "EXECUTION_ROUTE": "paper",
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
        broker_adapter=cast("BrokerAdapter", adapter),
        simulation_dispatch=None,
        live_session=session,
    )

    outcome = await run_live_evaluation_cycle(deps, evaluation_evidence())

    assert outcome.status == "sent"
    assert calls == ["data.market", "data.account", "indicators", "strategy", "risk"]
    assert adapter.calls == 1
    assert adapter.request is not None
    assert adapter.request.quantity == Decimal("0.50")
    assert len(audits) == 1
    assert deps.store.load_projection(("paper", "account-001", "mt5")) is not None
