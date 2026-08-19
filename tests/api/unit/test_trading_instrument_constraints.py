"""Trading instrument-constraint boundary tests."""

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.api.widgets.trading import routes


def test_constraints_preserve_provider_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """The UI contract receives exact metadata and registered route capability."""
    monkeypatch.setattr(routes, "require_human_permission", lambda *_args: None)
    monkeypatch.setattr(routes, "resolve_runtime_source_id", lambda **_kwargs: "mt5")
    metadata = SimpleNamespace(
        provider_symbol="EURUSD",
        volume_min=Decimal("0.01"),
        volume_max=Decimal(50),
        volume_step=Decimal("0.01"),
        price_step=Decimal("0.00001"),
        digits=5,
        pip_size=Decimal("0.0001"),
        trade_tick_size=Decimal("0.00001"),
        trade_tick_value_profit=Decimal("1.00"),
        trade_tick_value_loss=Decimal("1.00"),
        trade_contract_size=Decimal(100000),
        currency_profit="USD",
        trade_stops_level=10,
        retrieved_at=datetime(2026, 8, 17, tzinfo=UTC),
    )
    monkeypatch.setattr(
        routes,
        "get_symbol_metadata",
        lambda _request: SimpleNamespace(status="success", data=metadata),
    )
    monkeypatch.setattr(
        routes, "build_symbol_metadata_request", lambda **kwargs: kwargs
    )
    capability = SimpleNamespace(
        capability=SimpleNamespace(value="place_order"),
        supported_order_types=("MARKET", "LIMIT", "STOP", "STOP_LIMIT"),
        supported_time_in_force=("IOC", "FOK"),
    )
    monkeypatch.setattr(
        routes,
        "get_broker_capability_catalogue",
        lambda: SimpleNamespace(data={"mt5": (capability,)}),
    )

    result = routes._get_instrument_constraints(
        "EURUSD",
        SimpleNamespace(),
    )

    assert result.quantity_unit == "lots"
    assert result.min_quantity == Decimal("0.01")
    assert result.quantity_step == Decimal("0.01")
    assert result.digits == 5
    assert result.pip_size == Decimal("0.0001")
    assert result.trade_tick_value_profit == Decimal("1.00")
    assert result.trade_tick_value_loss == Decimal("1.00")
    assert result.trade_contract_size == Decimal(100000)
    assert result.profit_currency == "USD"
    assert result.supported_order_types == ("MARKET", "LIMIT", "STOP", "STOP_LIMIT")
    assert result.supported_time_in_force == ("IOC", "FOK")


def test_constraints_keep_incomplete_calculator_evidence_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing optional calculator values remain null without guessed defaults."""
    monkeypatch.setattr(routes, "require_human_permission", lambda *_args: None)
    monkeypatch.setattr(routes, "resolve_runtime_source_id", lambda **_kwargs: "mt5")
    metadata = SimpleNamespace(
        provider_symbol="EURUSD",
        volume_min=Decimal("0.01"),
        volume_max=Decimal(50),
        volume_step=Decimal("0.01"),
        price_step=Decimal("0.00001"),
        trade_stops_level=10,
        retrieved_at=datetime(2026, 8, 17, tzinfo=UTC),
    )
    monkeypatch.setattr(
        routes,
        "get_symbol_metadata",
        lambda _request: SimpleNamespace(status="success", data=metadata),
    )
    monkeypatch.setattr(
        routes, "build_symbol_metadata_request", lambda **kwargs: kwargs
    )
    capability = SimpleNamespace(
        capability=SimpleNamespace(value="place_order"),
        supported_order_types=("MARKET",),
        supported_time_in_force=("IOC",),
    )
    monkeypatch.setattr(
        routes,
        "get_broker_capability_catalogue",
        lambda: SimpleNamespace(data={"mt5": (capability,)}),
    )

    result = routes._get_instrument_constraints("EURUSD", SimpleNamespace())

    assert result.pip_size is None
    assert result.trade_tick_value_profit is None
    assert result.trade_tick_value_loss is None
    assert result.profit_currency is None
