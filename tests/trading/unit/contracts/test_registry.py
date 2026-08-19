"""Unit tests for the exact Trading public API registry."""

# ruff: noqa: INP001
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.services import trading
from app.services.trading import (
    create_trading_action_draft,
    get_public_contracts,
)


def _draft_data() -> dict[str, object]:
    """Return JSON-safe request material for a non-executable draft."""
    now = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
    return {
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
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
    """Catalog symbols exactly match the domain-root function exports."""
    catalog = get_public_contracts()
    assert catalog.status == "success"
    assert catalog.data is not None
    symbols = {str(entry["symbol"]) for entry in catalog.data}
    assert symbols == set(trading.__all__)


def test_domain_root_exports_are_explicit_and_import_safe() -> None:
    """The package root exposes every feature through an explicit stable list."""
    assert "submit_order" in trading.__all__
    assert "build_trading_report" in trading.__all__
    assert "create_live_session" in trading.__all__
    assert all(callable(getattr(trading, name)) for name in trading.__all__)
    # Resolution may be lazy, but the surface must stay declared: every public
    # name comes from an explicit table, and nothing outside it resolves.
    assert set(trading.__all__) == set(trading._EXPORTS)
    with pytest.raises(AttributeError):
        trading.definitely_not_a_trading_export  # noqa: B018


def test_domain_import_has_no_external_or_persistent_side_effect() -> None:
    """The package root contains no direct external side-effect calls."""
    source = (Path(__file__).parents[4] / "app/services/trading/__init__.py").read_text(
        encoding="utf-8"
    )
    forbidden = ("sqlite3.connect", "socket.connect", "subprocess.", "open(")
    assert all(token not in source for token in forbidden)
    assert trading.__all__


def test_create_draft_has_no_side_effect() -> None:
    """Draft creation packages validated data without a route authority call."""
    envelope = create_trading_action_draft(_draft_data())
    assert envelope.status == "success"
    assert envelope.metadata.extensions["side_effect_classification"] == "none"
    invalid = _draft_data()
    invalid.pop("approval_token_ref")
    captured = create_trading_action_draft(invalid)
    assert captured.status == "error"
    assert captured.error is not None
    assert captured.error.code == "INVALID_DRAFT"


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
    assert envelope.data is not None
    assert "s3cr3t" not in json.dumps(envelope.model_dump(mode="json"))
    assert envelope.metadata.extensions["redaction_applied"] is True
