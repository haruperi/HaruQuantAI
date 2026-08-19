"""Provider-authored Trading account-profile composition tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from types import MappingProxyType, SimpleNamespace

import pytest
from app.services import brokers
from app.services.api.widgets.trading import orchestration

_AUTH = SimpleNamespace(
    principal_id="profile-user",
    tenant_or_environment="development",
)


@pytest.fixture(autouse=True)
def _empty_session_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep account-profile tests independent from the runtime session database."""
    monkeypatch.setattr(
        orchestration, "resolve_active_execution_session", lambda **_: None
    )
    monkeypatch.setattr(orchestration, "list_execution_sessions", lambda **_: ())


def test_sim_profile_never_opens_mt5(monkeypatch: pytest.MonkeyPatch) -> None:
    """SIM presents explicit Simulator identity without broker access."""
    monkeypatch.setattr(orchestration, "resolve_execution_route", lambda **_k: "sim")
    monkeypatch.setattr(
        orchestration,
        "get_username_for_principal",
        lambda *_args, **_kwargs: "profile-user",
    )

    async def _unexpected(_route: str) -> object:
        raise AssertionError("SIM must not open MT5")

    monkeypatch.setattr(orchestration, "_connect_mode_broker", _unexpected)
    monkeypatch.setattr(
        orchestration,
        "resolve_active_execution_session",
        lambda **_: SimpleNamespace(
            name="Research SIM",
            sim_initial_balance=Decimal(25000),
            sim_leverage=50,
            sim_account_currency="USD",
        ),
    )
    result = asyncio.run(orchestration.build_trading_account_profile_source()(_AUTH))
    assert result.account_name == "profile-user"
    assert result.session_name == "Research SIM"
    assert result.trade_mode == "SIMULATION"
    assert result.source == "simulator"
    assert result.balance == Decimal(25000)
    assert result.equity == Decimal(25000)
    assert result.profit == Decimal(0)
    assert result.margin == Decimal(0)
    assert result.free_margin == Decimal(25000)
    assert result.leverage == Decimal(50)


def test_demo_profile_uses_mt5_name_and_trade_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MT5's name and DEMO mode become the exact displayed profile."""
    adapter = object()
    disconnected: list[object] = []
    monkeypatch.setattr(orchestration, "resolve_execution_route", lambda **_k: "demo")
    monkeypatch.setattr(
        orchestration,
        "resolve_active_execution_session",
        lambda **_: SimpleNamespace(name="London Demo"),
    )

    async def _connect(_route: str) -> object:
        return adapter

    async def _account(_adapter: object) -> object:
        return SimpleNamespace(
            status="success",
            data=SimpleNamespace(
                details=MappingProxyType(
                    {
                        "name": "Rufaro MT5",
                        "trade_mode": "DEMO",
                        "profit": 125.5,
                        "margin_level": 812.25,
                        "leverage": 100,
                    }
                ),
                currency="USD",
                balance=Decimal(100000),
                equity=Decimal("100125.5"),
                margin=Decimal(12325),
                free_margin=Decimal("87800.5"),
                retrieved_at=datetime(2026, 8, 17, tzinfo=UTC),
            ),
        )

    async def _disconnect(value: object) -> None:
        disconnected.append(value)

    monkeypatch.setattr(brokers, "get_broker_account_info", _account)
    monkeypatch.setattr(brokers, "disconnect_broker", _disconnect)
    result = asyncio.run(
        orchestration.build_trading_account_profile_source(_connect)(_AUTH)
    )
    assert result.account_name == "Rufaro MT5"
    assert result.session_name == "London Demo"
    assert result.environment_label == "Demo Environment"
    assert result.balance == Decimal(100000)
    assert result.equity == Decimal("100125.5")
    assert result.profit == Decimal("125.5")
    assert result.margin == Decimal(12325)
    assert result.free_margin == Decimal("87800.5")
    assert result.margin_level == Decimal("812.25")
    assert result.leverage == Decimal(100)
    assert disconnected == [adapter]


def test_mt5_profile_displays_provider_mode_during_election_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read-only identity displays MT5 truth while execution stays fail-closed."""
    disconnected: list[object] = []
    monkeypatch.setattr(orchestration, "resolve_execution_route", lambda **_k: "live")

    async def _connect(_route: str) -> object:
        return "adapter"

    async def _account(_adapter: object) -> object:
        return SimpleNamespace(
            status="success",
            data=SimpleNamespace(
                details={
                    "name": "Demo Account",
                    "trade_mode": "DEMO",
                    "profit": None,
                    "margin_level": None,
                    "leverage": None,
                },
                currency=None,
                balance=None,
                equity=None,
                margin=None,
                free_margin=None,
                retrieved_at=datetime(2026, 8, 17, tzinfo=UTC),
            ),
        )

    async def _disconnect(value: object) -> None:
        disconnected.append(value)

    monkeypatch.setattr(orchestration, "_connect_mode_broker", _connect)
    monkeypatch.setattr(brokers, "get_broker_account_info", _account)
    monkeypatch.setattr(brokers, "disconnect_broker", _disconnect)
    result = asyncio.run(orchestration.build_trading_account_profile_source()(_AUTH))
    assert result.account_name == "Demo Account"
    assert result.trade_mode == "DEMO"
    assert result.environment_label == "Demo Environment"
    assert disconnected == ["adapter"]


def test_mt5_profile_rejects_missing_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing provider identity is unavailable rather than replaced by login."""
    monkeypatch.setattr(orchestration, "resolve_execution_route", lambda **_k: "demo")

    async def _connect(_route: str) -> object:
        return object()

    async def _account(_adapter: object) -> object:
        return SimpleNamespace(
            status="success",
            data=SimpleNamespace(
                details={"name": "N/A", "trade_mode": "DEMO"},
                retrieved_at=datetime(2026, 8, 17, tzinfo=UTC),
            ),
        )

    async def _disconnect(_adapter: object) -> None:
        return None

    monkeypatch.setattr(orchestration, "_connect_mode_broker", _connect)
    monkeypatch.setattr(brokers, "get_broker_account_info", _account)
    monkeypatch.setattr(brokers, "disconnect_broker", _disconnect)
    with pytest.raises(RuntimeError, match="TRADING_ACCOUNT_PROFILE_MALFORMED"):
        asyncio.run(orchestration.build_trading_account_profile_source()(_AUTH))
