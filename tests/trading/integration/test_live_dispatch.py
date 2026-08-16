"""Workflow integration for real Risk enforcement before live dispatch."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.services.trading import (
    create_live_session,
    create_readiness_assessment,
    evaluate_live_gate,
    start_live_session,
    submit_order,
)

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

    async def place_order(self, request: object) -> object:
        """Record adapter invocation and acknowledge the placement."""
        self.order.append("adapter")
        return await super().place_order(request)


async def _passed() -> bool:
    """Return successful lifecycle evidence."""
    return True


def _demo_session(
    adapter: _AuditedAdapter,
    store: MemoryStore,
    order: list[str],
    *,
    include_risk: bool = True,
) -> Any:
    """Build a demo session with every real mutation gate injected."""
    connection = broker_connection()
    return create_live_session(
        store=store,
        connection=connection,
        broker_adapter=cast("object", adapter),
        feature_flags=SimpleNamespace(broker_id="mt5", environment="demo"),
        risk_decision_source=(
            (lambda _request: live_risk_decision())
            if include_risk
            else (lambda _request: None)
        ),
        action_policy_source=lambda _request: live_action_policy(),
        kill_switch_source=inactive_kill_switch_hierarchy,
        readiness_source=lambda request, _evidence: create_readiness_assessment(
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
    await start_live_session(session, config, live_evidence())
    blocked_gate = await evaluate_live_gate(
        live_gate_request(), {"risk_approved": True}, session
    )
    assert blocked_gate.status == "error"
    assert blocked_gate.error is not None
    assert blocked_gate.error.code == "GATE_BLOCKED"


@pytest.mark.anyio
async def test_live_dispatch_completes_single_broker_mutation() -> None:
    """A fully gated demo request performs one audited Broker mutation."""
    request_data = live_gate_request().model_dump(mode="python")
    request_data.update({"route": "demo", "provider_id": "mt5"})
    request = type(live_gate_request()).model_validate(request_data)
    store = MemoryStore()
    ordering: list[str] = []
    adapter = _AuditedAdapter(ordering)
    session = _demo_session(adapter, store, ordering)
    config = {
        **live_config(),
        "RUNTIME_PROFILE": "demo",
        "EXECUTION_ROUTE": "demo",
        "ALLOW_LIVE_MUTATIONS": True,
    }
    await start_live_session(session, config, live_evidence())
    deps = replace(
        trading_dependencies(store=store),
        connection=broker_connection(),
        broker_adapter=cast("object", adapter),
        live_session=session,
    )

    outcome = await submit_order(request, deps)

    assert adapter.calls == 1
    assert outcome.status == "success"
    assert outcome.metadata.extensions["legacy_status"] == "sent"
    assert [event.event_type for event in store.events] == [
        "send_attempted",
        "receipt_recorded",
    ]
    assert ordering == ["pre_audit", "adapter"]

    blocked_adapter = _AuditedAdapter([])
    blocked_session = _demo_session(
        blocked_adapter, MemoryStore(), [], include_risk=False
    )
    await start_live_session(blocked_session, config, live_evidence())
    blocked_deps = replace(
        trading_dependencies(store=MemoryStore()),
        connection=broker_connection(),
        broker_adapter=cast("object", blocked_adapter),
        live_session=blocked_session,
    )
    blocked = await submit_order(request, blocked_deps)
    assert blocked.status == "error"
    assert blocked.error is not None
    assert blocked.error.code == "GATE_BLOCKED"
    assert blocked_adapter.calls == 0
