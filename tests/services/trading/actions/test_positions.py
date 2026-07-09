"""Unit tests for position action primitives."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.actions.positions import (
    NettingMode,
    ReduceExposureScope,
    position_close,
    position_modify,
    position_open,
    reduce_exposure,
)
from app.services.trading.actions.validation import OrderSide
from app.services.trading.contracts import TradingStatus
from app.services.trading.security.error_mapping import TradingMappedError

from tests.services.trading.actions._fixtures import (
    ROUTE_KWARGS,
    as_dict,
    build_context,
    build_deps,
)


def test_position_open_delegates_to_buy_or_sell() -> None:
    """position_open opens via buy or sell depending on side."""
    context = build_context()
    deps = build_deps()
    buy_side = position_open(
        symbol="EURUSD",
        side=OrderSide.BUY,
        volume=Decimal("0.10"),
        deviation_points=10,
        request_id="req-1",
        correlation_id="corr-1",
        context=context,
        deps=deps,
        **ROUTE_KWARGS,
    )
    sell_side = position_open(
        symbol="EURUSD",
        side=OrderSide.SELL,
        volume=Decimal("0.10"),
        deviation_points=10,
        request_id="req-2",
        correlation_id="corr-2",
        context=context,
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert buy_side.status is TradingStatus.ACCEPTED
    assert sell_side.status is TradingStatus.ACCEPTED


def test_position_close_requires_ticket_or_symbol() -> None:
    """position_close requires at least one addressing mode."""
    deps = build_deps()
    with pytest.raises(TradingMappedError):
        position_close(
            netting_mode=NettingMode.NETTING,
            request_id="req-1",
            correlation_id="corr-1",
            deps=deps,
            **ROUTE_KWARGS,
        )


def test_position_close_hedging_requires_ticket() -> None:
    """Hedging-mode close requires an explicit ticket even with a symbol."""
    deps = build_deps()
    with pytest.raises(TradingMappedError):
        position_close(
            netting_mode=NettingMode.HEDGING,
            symbol="EURUSD",
            request_id="req-2",
            correlation_id="corr-2",
            deps=deps,
            **ROUTE_KWARGS,
        )
    response = position_close(
        netting_mode=NettingMode.HEDGING,
        ticket="123",
        symbol="EURUSD",
        request_id="req-3",
        correlation_id="corr-3",
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert response.status is TradingStatus.ACCEPTED


def test_position_close_by_symbol_in_netting_mode() -> None:
    """Netting-mode close accepts symbol-only addressing."""
    deps = build_deps()
    response = position_close(
        netting_mode=NettingMode.NETTING,
        symbol="EURUSD",
        volume=Decimal("0.05"),
        request_id="req-4",
        correlation_id="corr-4",
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert response.status is TradingStatus.ACCEPTED


def test_position_modify_requires_position_id() -> None:
    """position_modify rejects a blank position identifier."""
    deps = build_deps()
    with pytest.raises(TradingMappedError):
        position_modify(
            position_id=" ",
            request_id="req-1",
            correlation_id="corr-1",
            deps=deps,
            **ROUTE_KWARGS,
        )
    response = position_modify(
        position_id="pos-1",
        sl=Decimal("1.09000"),
        tp=Decimal("1.11000"),
        expected_state_version=2,
        request_id="req-2",
        correlation_id="corr-2",
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert response.status is TradingStatus.ACCEPTED


def test_reduce_exposure_validates_inputs() -> None:
    """reduce_exposure requires a target, risk decision, and positive volume."""
    deps = build_deps()
    with pytest.raises(TradingMappedError):
        reduce_exposure(
            scope=ReduceExposureScope.SYMBOL,
            target=" ",
            volume=Decimal("0.10"),
            risk_decision_id="risk-1",
            request_id="req-1",
            correlation_id="corr-1",
            deps=deps,
            **ROUTE_KWARGS,
        )
    with pytest.raises(TradingMappedError):
        reduce_exposure(
            scope=ReduceExposureScope.SYMBOL,
            target="EURUSD",
            volume=Decimal("0.10"),
            risk_decision_id=" ",
            request_id="req-2",
            correlation_id="corr-2",
            deps=deps,
            **ROUTE_KWARGS,
        )
    with pytest.raises(TradingMappedError):
        reduce_exposure(
            scope=ReduceExposureScope.SYMBOL,
            target="EURUSD",
            volume=Decimal(0),
            risk_decision_id="risk-1",
            request_id="req-3",
            correlation_id="corr-3",
            deps=deps,
            **ROUTE_KWARGS,
        )
    response = reduce_exposure(
        scope=ReduceExposureScope.SYMBOL,
        target="EURUSD",
        volume=Decimal("0.05"),
        risk_decision_id="risk-1",
        request_id="req-4",
        correlation_id="corr-4",
        deps=deps,
        **ROUTE_KWARGS,
    )
    assert response.status is TradingStatus.ACCEPTED
    assert as_dict(response.data["dispatch_payload"])["scope"] == "symbol"
