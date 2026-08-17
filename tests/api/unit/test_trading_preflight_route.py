"""Unit evidence for the manual-order Risk preflight dispatcher."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.services.api.workstation.trading.orchestration import (
    build_trading_preflight_source,
)


def _request(**overrides: object) -> Any:
    """Build one minimal preflight boundary request stand-in."""
    values: dict[str, object] = {
        "route": "demo",
        "account_id": "account-one",
        "symbol": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": 1,
        "current_price": 1.1,
        "stop_distance": None,
        "portfolio_id": None,
        "request_id": "req-one",
        "workflow_id": "wf-one",
        "correlation_id": "cor-one",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_live_routing_reaches_the_real_risk_path_like_any_other_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live routing is not special-cased ahead of Risk.

    The boundary used to refuse a live order outright. It no longer does:
    Risk is the sole authority on whether one may proceed, so a live request
    must reach the same broker and review path demo does. Reaching the broker
    connection is what proves no pre-emptive refusal survives.
    """
    import app.services.brokers as brokers_module

    connected: list[object] = []

    async def _connect(*args: object, **_kwargs: object) -> object:
        connected.append(args)
        raise RuntimeError("BROKER_PROBE")

    monkeypatch.setattr(brokers_module, "create_connected_broker", _connect)
    source = build_trading_preflight_source()

    with pytest.raises(RuntimeError, match="BROKER_PROBE"):
        asyncio.run(source(_request(route="live"), auth=SimpleNamespace()))
    assert connected, "a live request must reach the real broker path"


def test_preflight_fails_closed_when_the_account_snapshot_is_unavailable(
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
    source = build_trading_preflight_source()

    with pytest.raises(RuntimeError, match="ACCOUNT_SNAPSHOT_UNAVAILABLE"):
        asyncio.run(source(_request(), auth=SimpleNamespace()))


def test_preflight_returns_the_real_decision_and_verdict_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A successful review maps the real decision/verdict onto the response shape."""
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
        state=SimpleNamespace(value="needs_approval"),
        decision_id="decision-one",
        token=None,
        composite_breach_flags=("approval_required",),
        expires_at=datetime(2026, 8, 14, tzinfo=UTC),
    )
    monkeypatch.setattr(
        risk_module, "review_manual_order", lambda **_k: (decision, None)
    )
    source = build_trading_preflight_source()

    result = cast(
        "dict[str, object]", asyncio.run(source(_request(), auth=SimpleNamespace()))
    )

    assert result["state"] == "needs_approval"
    assert result["risk_decision_id"] == "decision-one"
    assert result["approval_token_ref"] is None
    assert result["action_policy_verdict_id"] is None
    assert result["reasons"] == ("approval_required",)
