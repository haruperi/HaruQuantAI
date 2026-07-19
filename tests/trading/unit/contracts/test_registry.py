"""Unit tests for the exact Trading public API registry."""

# ruff: noqa: INP001

import json
from datetime import UTC, datetime, timedelta

import pytest
from app.services import trading
from app.services.trading import contracts
from app.services.trading.contracts import (
    TradingError,
    create_trading_action_draft,
    get_public_contracts,
)


def _draft_data() -> dict[str, object]:
    """Return JSON-safe request material for a non-executable draft."""
    now = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
    return {
        "request_id": "req-draft-001",
        "workflow_id": "wf-draft-001",
        "correlation_id": "corr-draft-001",
        "route": "sim",
        "action": "submit_order",
        "provider_id": None,
        "account_id": "account-001",
        "strategy_id": "strategy-001",
        "strategy_version": "v1",
        "intent_id": "source-intent-001",
        "symbol": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity_unit": "units",
        "quantity": "1.00",
        "risk_decision_id": "risk-001",
        "action_policy_verdict_id": "verdict-001",
        "approval_token_ref": "approval-001",
        "idempotency_key": "caller-key-001",
        "canonical_material_version": "v1",
        "system_time": now,
        "valid_until": now + timedelta(minutes=5),
    }


def test_public_catalog_matches_exports() -> None:
    """Catalog symbols exactly match approved contracts package exports."""
    symbols = {str(entry["symbol"]) for entry in get_public_contracts()}
    assert symbols == set(contracts.__all__)


def test_domain_root_exports_are_explicit_and_import_safe() -> None:
    """The package root exposes every feature through an explicit stable list."""
    assert "submit_order" in trading.__all__
    assert "build_trading_report" in trading.__all__
    assert "LiveSession" in trading.__all__
    assert not hasattr(trading, "__getattr__")


def test_create_draft_has_no_side_effect() -> None:
    """Draft creation packages validated data without a route authority call."""
    envelope = create_trading_action_draft(_draft_data())
    assert envelope.status == "packaged"
    assert envelope.audit_metadata["side_effect_classification"] == "none"
    invalid = _draft_data()
    invalid.pop("approval_token_ref")
    with pytest.raises(TradingError) as captured:
        create_trading_action_draft(invalid)
    assert captured.value.trading_code == "INVALID_DRAFT"


def test_create_draft_redacts_sensitive_text_before_return() -> None:
    """Draft output cannot leak secret-like values from valid text fields."""
    data = _draft_data()
    data.update(
        {
            "action": "trigger_kill_switch",
            "scope_level": "global",
            "control_reason": "password=s3cr3t",
        }
    )
    envelope = create_trading_action_draft(data)
    assert "s3cr3t" not in json.dumps(envelope.model_dump(mode="json"))
    assert envelope.audit_metadata["redaction_applied"] is True
