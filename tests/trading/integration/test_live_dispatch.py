"""Workflow integration for real Risk enforcement before live dispatch."""

# ruff: noqa: INP001
from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import pytest
from app.services.brokers import (
    BrokerAdapter,
    BrokerFeatureFlags,
    BrokerOrderRequest,
    BrokerOrderResult,
)
from app.services.trading import (
    LiveSession,
    ReadinessAssessment,
    TradingError,
    evaluate_live_gate,
    submit_order,
)
from app.utils import StandardResponse
from tests.trading.conftest import (
    CountingAdapter,
    MemoryStore,
    auth_context,
    broker_connection,
    inactive_kill_switch_hierarchy,
    live_action_policy,
    live_config,
    live_evidence,
    live_gate_request,
    live_gate_session,
    live_risk_decision,
    symbol_capability,
    trading_dependencies,
)


class _AuditedAdapter(CountingAdapter):
    """Broker adapter that records mutation ordering beside pre-audit evidence."""

    def __init__(self, order: list[str]) -> None:
        """Initialize the adapter with a shared ordering recorder."""
        super().__init__()
        self.order = order

    async def place_order(
        self, request: BrokerOrderRequest
    ) -> StandardResponse[BrokerOrderResult]:
        """Record adapter invocation and acknowledge the placement."""
        self.order.append("adapter")
        return await super().place_order(request)


async def _passed() -> bool:
    """Return successful lifecycle evidence."""
    return True


def _paper_session(
    adapter: _AuditedAdapter,
    store: MemoryStore,
    order: list[str],
    *,
    include_risk: bool = True,
) -> LiveSession:
    """Build a paper session with every real mutation gate injected."""
    connection = broker_connection()
    return LiveSession(
        store=store,
        connection=connection,
        broker_adapter=cast("BrokerAdapter", adapter),
        feature_flags=cast(
            "BrokerFeatureFlags",
            SimpleNamespace(
                broker_id=connection.broker_id,
                environment=connection.environment,
            ),
        ),
        risk_decision_source=(
            (lambda _request: live_risk_decision())
            if include_risk
            else (lambda _request: None)
        ),
        action_policy_source=lambda _request: live_action_policy(),
        kill_switch_source=inactive_kill_switch_hierarchy,
        readiness_source=lambda request, _evidence: ReadinessAssessment(
            passed=True,
            failed_check_codes=(),
            evidence_refs={"data_authority_id": "data-authority-001"},
            assessed_at=request.system_time,
        ),
        adapter_capability_source=lambda request: symbol_capability(
            request.route, request.provider_id, request.symbol
        )[0],
        auth_context_source=auth_context,
        pre_audit_sink=lambda _evidence: order.append("pre_audit"),
        event_sink=lambda _event: None,
        startup_reconcile=_passed,
        drain_in_flight=_passed,
        flush_evidence=_passed,
        shutdown_reconcile=_passed,
        clock=lambda: live_gate_request().system_time,
    )


@pytest.mark.anyio
async def test_live_dispatch_requires_real_risk_decision() -> None:
    """No caller facts can substitute for the typed current Risk decision."""
    session = live_gate_session(risk_decision=None)
    config = {**live_config(), "ALLOW_LIVE_MUTATIONS": True}
    await session.start(config, live_evidence())
    with pytest.raises(TradingError, match="GATE_BLOCKED"):
        await evaluate_live_gate(live_gate_request(), {"risk_approved": True}, session)


@pytest.mark.anyio
async def test_live_dispatch_completes_single_broker_mutation() -> None:
    """A fully gated paper request performs one audited Broker mutation."""
    request_data = live_gate_request().model_dump(mode="python")
    request_data.update({"route": "paper", "provider_id": "mt5"})
    request = type(live_gate_request()).model_validate(request_data)
    store = MemoryStore()
    ordering: list[str] = []
    adapter = _AuditedAdapter(ordering)
    session = _paper_session(adapter, store, ordering)
    config = {
        **live_config(),
        "RUNTIME_PROFILE": "paper",
        "EXECUTION_ROUTE": "paper",
        "ALLOW_LIVE_MUTATIONS": True,
    }
    await session.start(config, live_evidence())
    deps = replace(
        trading_dependencies(store=store),
        connection=broker_connection(),
        broker_adapter=cast("BrokerAdapter", adapter),
        simulation_dispatch=None,
        live_session=session,
    )

    outcome = await submit_order(request, deps)

    assert adapter.calls == 1
    assert outcome.status == "sent"
    assert [event.event_type for event in store.events] == [
        "send_attempted",
        "receipt_recorded",
    ]
    assert ordering == ["pre_audit", "adapter"]

    blocked_adapter = _AuditedAdapter([])
    blocked_session = _paper_session(
        blocked_adapter, MemoryStore(), [], include_risk=False
    )
    await blocked_session.start(config, live_evidence())
    blocked_deps = replace(
        trading_dependencies(store=MemoryStore()),
        connection=broker_connection(),
        broker_adapter=cast("BrokerAdapter", blocked_adapter),
        simulation_dispatch=None,
        live_session=blocked_session,
    )
    with pytest.raises(TradingError, match="GATE_BLOCKED"):
        await submit_order(request, blocked_deps)
    assert blocked_adapter.calls == 0
