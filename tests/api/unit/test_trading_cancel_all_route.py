"""Unit evidence for the bulk cancel-all Risk preflight dispatcher."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.services.api.workstation.trading.orchestration import (
    build_trading_cancel_all_preflight_source,
)


def _request(**overrides: object) -> Any:
    """Build one minimal bulk cancel-all preflight boundary request stand-in."""
    values: dict[str, object] = {
        "route": "demo",
        "account_id": "account-one",
        "portfolio_id": None,
        "representative_symbol": "EURUSD",
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

    The boundary used to refuse a live bulk cancellation outright. It no longer does:
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
    source = build_trading_cancel_all_preflight_source()

    with pytest.raises(RuntimeError, match="BROKER_PROBE"):
        asyncio.run(source(_request(route="live"), auth=SimpleNamespace()))
    assert connected, "a live request must reach the real broker path"


def test_cancel_all_preflight_fails_closed_when_the_account_snapshot_is_unavailable(
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
    source = build_trading_cancel_all_preflight_source()

    with pytest.raises(RuntimeError, match="ACCOUNT_SNAPSHOT_UNAVAILABLE"):
        asyncio.run(source(_request(), auth=SimpleNamespace()))


def test_cancel_all_preflight_returns_the_real_decision_and_verdict_mapping(
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

    def _fake_config(*_args: object, **_kwargs: object) -> object:
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
    monkeypatch.setattr(
        risk_module,
        "review_cancel_authorization",
        lambda **_k: (decision, verdict),
    )
    source = build_trading_cancel_all_preflight_source()

    result = cast(
        "dict[str, object]", asyncio.run(source(_request(), auth=SimpleNamespace()))
    )

    assert result["state"] == "approve"
    assert result["risk_decision_id"] == "decision-one"
    assert result["approval_token_ref"] == "token-one"
    assert result["action_policy_verdict_id"] == "verdict-one"
    assert result["reasons"] == ()
