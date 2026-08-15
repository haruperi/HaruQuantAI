"""Public approved-request builder convergence tests."""

from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast

from app.services.trading import build_approved_trading_request

from tests.trading.unit.actions.test_dependencies import dependencies
from tests.trading.unit.actions.test_runtime import (
    evidence,
    risk_decision,
    trade_intent,
)


def _dependencies() -> Any:
    """Return dependencies with the selected simulation lifecycle route."""
    return replace(
        dependencies(),
        live_session=cast(
            "object", SimpleNamespace(config=SimpleNamespace(execution_route="sim"))
        ),
    )


def test_builder_preserves_only_risk_approved_economics() -> None:
    """The public builder uses exact Strategy/Risk lineage and approved size."""
    request = build_approved_trading_request(
        trade_intent(), risk_decision(), _dependencies(), evidence()
    )
    assert request.quantity == Decimal("0.50")
    assert request.intent_id == "intent-001"
    assert request.risk_decision_id == "risk-001"
    assert request.route.value == "sim"
    assert request.contract_version == "v2"
    assert request.fill_policy == "FOK"
    assert request.time_policy == "GTC"
    assert request.provider_specification_checksum == "b" * 64


def test_trace_renaming_does_not_change_approved_economic_fields() -> None:
    """Trace identity changes leave the approved economic projection identical."""
    baseline = build_approved_trading_request(
        trade_intent(), risk_decision(), _dependencies(), evidence()
    )
    decision = risk_decision().model_copy(
        update={
            "request_id": "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "workflow_id": "wf-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            "correlation_id": "cor-cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        }
    )
    changed = build_approved_trading_request(
        trade_intent(), decision, _dependencies(), evidence()
    )
    excluded = {"request_id", "workflow_id", "correlation_id"}
    baseline_fields = baseline.model_dump(exclude=excluded)
    changed_fields = changed.model_dump(exclude=excluded)
    assert baseline_fields == changed_fields
