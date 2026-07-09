"""Unit tests for emergency action primitives."""

from __future__ import annotations

from app.services.trading.actions.emergency import (
    EmergencyScope,
    cancel_all_orders,
    close_all_positions,
    flatten_account,
    flatten_strategy,
    flatten_symbol,
)
from app.services.trading.contracts import SideEffectMode, TradingStatus

from tests.services.trading.actions._fixtures import ROUTE_KWARGS, as_dict, build_deps


def test_cancel_all_orders_snapshots_and_packages() -> None:
    """cancel_all_orders snapshots scope state and packages child actions."""
    deps = build_deps()
    response = cancel_all_orders(
        scope=EmergencyScope.ACCOUNT,
        target=None,
        request_id="req-1",
        correlation_id="corr-1",
        deps=deps,
        **ROUTE_KWARGS,
    )
    dispatch_payload = as_dict(response.data["dispatch_payload"])
    assert response.status is TradingStatus.ACCEPTED
    assert response.side_effect_mode is SideEffectMode.PACKAGED_ONLY
    assert "pre_snapshot" in dispatch_payload
    assert "child_actions" in dispatch_payload


def test_close_all_positions_scoped_by_symbol() -> None:
    """close_all_positions accepts a symbol-scoped target."""
    deps = build_deps()
    response = close_all_positions(
        scope=EmergencyScope.SYMBOL,
        target="EURUSD",
        request_id="req-2",
        correlation_id="corr-2",
        deps=deps,
        **ROUTE_KWARGS,
    )
    dispatch_payload = as_dict(response.data["dispatch_payload"])
    assert response.status is TradingStatus.ACCEPTED
    assert dispatch_payload["scope"] == "symbol"
    assert dispatch_payload["target"] == "EURUSD"


def test_flatten_account_combines_cancel_and_close() -> None:
    """flatten_account packages both a cancel-all and a close-all result."""
    deps = build_deps()
    response = flatten_account(
        request_id="req-3",
        correlation_id="corr-3",
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert response.status is TradingStatus.ACCEPTED
    assert "cancel_result" in response.data
    assert "close_result" in response.data


def test_flatten_strategy_and_symbol_scope_targets() -> None:
    """flatten_strategy/flatten_symbol pass their scope target through."""
    deps = build_deps()
    strategy_response = flatten_strategy(
        strategy_id="99001",
        request_id="req-4",
        correlation_id="corr-4",
        deps=deps,
        **ROUTE_KWARGS,
    )
    symbol_response = flatten_symbol(
        symbol="EURUSD",
        request_id="req-5",
        correlation_id="corr-5",
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert strategy_response.status is TradingStatus.ACCEPTED
    assert symbol_response.status is TradingStatus.ACCEPTED

    strategy_cancel_result = as_dict(strategy_response.data["cancel_result"])
    strategy_cancel_data = as_dict(strategy_cancel_result["data"])
    strategy_dispatch_payload = as_dict(strategy_cancel_data["dispatch_payload"])
    assert strategy_dispatch_payload["scope"] == "strategy"

    symbol_cancel_result = as_dict(symbol_response.data["cancel_result"])
    symbol_cancel_data = as_dict(symbol_cancel_result["data"])
    symbol_dispatch_payload = as_dict(symbol_cancel_data["dispatch_payload"])
    assert symbol_dispatch_payload["scope"] == "symbol"
