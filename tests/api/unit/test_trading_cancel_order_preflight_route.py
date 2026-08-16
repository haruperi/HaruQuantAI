"""Unit evidence for the single-order cancellation Risk preflight dispatcher."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.services.api.workstation.trading.orchestration import (
    build_trading_cancel_order_preflight_source,
)


def _request(**overrides: object) -> Any:
    """Build one minimal single-order cancel preflight boundary request stand-in."""
    values: dict[str, object] = {
        "route": "paper",
        "account_id": "account-one",
        "portfolio_id": None,
        "representative_symbol": "EURUSD",
        "target_broker_order_id": "broker-order-one",
        "request_id": "req-one",
        "workflow_id": "wf-one",
        "correlation_id": "cor-one",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_cancel_order_preflight_refuses_live_routing_before_touching_a_broker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live routing is refused deterministically, with no broker connection attempt."""
    import app.services.brokers as brokers_module

    async def _fail_connect(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("must not connect a broker for a refused live request")

    monkeypatch.setattr(brokers_module, "create_connected_broker", _fail_connect)
    source = build_trading_cancel_order_preflight_source()

    with pytest.raises(RuntimeError, match="MANUAL_ORDER_LIVE_NOT_CONFIGURED"):
        asyncio.run(source(_request(route="live"), auth=SimpleNamespace()))


def test_cancel_order_preflight_fails_closed_when_the_account_snapshot_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unavailable real account snapshot never falls back to invented data."""
    import app.services.brokers as brokers_module
    import app.services.data as data_module

    async def _connect(*_args: object, **_kwargs: object) -> object:
        return SimpleNamespace()

    async def _disconnect(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(brokers_module, "create_connected_broker", _connect)
    monkeypatch.setattr(brokers_module, "disconnect_broker", _disconnect)
    monkeypatch.setattr(
        data_module, "build_account_snapshot_request", lambda **_k: object()
    )
    monkeypatch.setattr(
        data_module,
        "get_account_state_snapshot",
        lambda *_a, **_k: SimpleNamespace(status="error", data=None),
    )
    source = build_trading_cancel_order_preflight_source()

    with pytest.raises(RuntimeError, match="ACCOUNT_SNAPSHOT_UNAVAILABLE"):
        asyncio.run(source(_request(), auth=SimpleNamespace()))


def test_cancel_order_preflight_returns_the_real_decision_and_verdict_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A successful review maps the real decision/verdict onto the response shape,
    scoped to the exact target order rather than the whole account."""
    import app.services.brokers as brokers_module
    import app.services.data as data_module
    import app.services.risk as risk_module

    async def _connect(*_args: object, **_kwargs: object) -> object:
        return SimpleNamespace()

    async def _disconnect(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(brokers_module, "create_connected_broker", _connect)
    monkeypatch.setattr(brokers_module, "disconnect_broker", _disconnect)
    monkeypatch.setattr(
        data_module, "build_account_snapshot_request", lambda **_k: object()
    )
    snapshot = SimpleNamespace(account_id="account-one")
    monkeypatch.setattr(
        data_module,
        "get_account_state_snapshot",
        lambda *_a, **_k: SimpleNamespace(status="success", data=snapshot),
    )

    def _fake_config() -> object:
        return object()

    monkeypatch.setattr(risk_module, "build_personal_account_risk_config", _fake_config)
    decision = SimpleNamespace(
        state=SimpleNamespace(value="approve"),
        decision_id="decision-one",
        token=SimpleNamespace(token_id="token-one"),
        composite_breach_flags=(),
        expires_at=datetime(2026, 8, 14, tzinfo=UTC),
    )
    verdict = SimpleNamespace(verdict_id="verdict-one")
    seen: dict[str, object] = {}

    def _fake_review(**kwargs: object) -> tuple[object, object]:
        seen.update(kwargs)
        return decision, verdict

    monkeypatch.setattr(risk_module, "review_cancel_authorization", _fake_review)
    source = build_trading_cancel_order_preflight_source()

    result = cast(
        "dict[str, object]", asyncio.run(source(_request(), auth=SimpleNamespace()))
    )

    assert result["state"] == "approve"
    assert result["risk_decision_id"] == "decision-one"
    assert result["approval_token_ref"] == "token-one"
    assert result["action_policy_verdict_id"] == "verdict-one"
    assert seen["action"] == "cancel_order"
    assert seen["action_scope"] == {"target_broker_order_id": "broker-order-one"}
