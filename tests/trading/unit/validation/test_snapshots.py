"""Unit tests for explicit Trading route snapshots."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta

import pytest
from app.services.trading.contracts import TradingError, TradingRequest
from app.services.trading.validation import RouteSnapshot, get_route_snapshot
from pydantic import ValidationError

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _request() -> TradingRequest:
    """Build one canonical request for route fact reads."""
    return TradingRequest(
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        route="paper",
        action="submit_order",
        provider_id="provider-001",
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        intent_id="intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        quantity="1.00",
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        idempotency_key="key-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )


def _snapshot_data() -> dict[str, object]:
    """Build complete explicit route fact material."""
    return {
        "route": "paper",
        "provider_id": "provider-001",
        "account_id": "account-001",
        "symbol": "EURUSD",
        "facts": {"quote": {"bid": "1.0999", "ask": "1.1001"}},
        "source_id": "data-source-001",
        "authority_id": "broker-001",
        "observed_at": NOW,
        "expires_at": NOW + timedelta(seconds=30),
        "available": True,
        "fresh": True,
        "capabilities": ("submit_order",),
    }


def test_snapshot_never_substitutes_neutral_defaults() -> None:
    """Unavailable source evidence raises instead of returning neutral facts."""
    data = _snapshot_data()
    data["available"] = False
    with pytest.raises(TradingError) as captured:
        get_route_snapshot(_request(), lambda _route, _provider: data)  # type: ignore[arg-type,return-value]
    assert captured.value.trading_code == "SERVICE_UNAVAILABLE"
    with pytest.raises(TradingError) as malformed:
        get_route_snapshot(_request(), lambda _route, _provider: {})
    assert malformed.value.trading_code == "SERVICE_UNAVAILABLE"
    stale = _snapshot_data()
    stale["fresh"] = False
    with pytest.raises(TradingError) as stale_error:
        get_route_snapshot(_request(), lambda _route, _provider: stale)  # type: ignore[arg-type,return-value]
    assert stale_error.value.trading_code == "STALE_EVIDENCE"
    wrong_scope = _snapshot_data()
    wrong_scope["account_id"] = "other-account"
    with pytest.raises(TradingError) as scope_error:
        get_route_snapshot(_request(), lambda _route, _provider: wrong_scope)  # type: ignore[arg-type,return-value]
    assert scope_error.value.trading_code == "SCOPE_MISMATCH"


def test_route_snapshot_requires_provenance() -> None:
    """RouteSnapshot rejects missing source and authority provenance."""
    data = _snapshot_data()
    data.pop("source_id")
    with pytest.raises(ValidationError):
        RouteSnapshot.model_validate(data)
    duplicate = _snapshot_data()
    duplicate["capabilities"] = ("submit_order", "submit_order")
    with pytest.raises(ValidationError, match="unique"):
        RouteSnapshot.model_validate(duplicate)
