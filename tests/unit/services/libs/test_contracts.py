"""Unit tests for foundational trading data contracts and enums.

Description:
    Validates instantiation, default field states, methods, and strict absence of
    legacy alias shims across the canonical contracts and enums defined in
    app.services.libs.

Purpose:
    FEAT-LIBS-CONTRACTS: Core data contract verification.
    FEAT-LIBS-ENUMS: Canonical trading enumerations verification.

Key Capabilities:
    - FR-CONTRACTS-INSTANTIATION: Verify data contract defaults and field integrity.
    - FR-CONTRACTS-ROUNDING: Verify SymbolInfo.round_to_tick_size precision handling.
    - FR-CONTRACTS-ZERO-SHIMS: Verify strict absence of deprecated transitional aliases.
"""

from __future__ import annotations

from app.services.libs import contracts
from app.services.libs.contracts import (
    AccountInfo,
    BookInfo,
    DealInfo,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TerminalInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)
from app.services.libs.enums import (
    AccountTradeMode,
    BookType,
    DealEntry,
    DealType,
    MarginMode,
    OrderState,
    OrderType,
    PositionType,
    TradeAction,
    TradeRetcode,
)


def test_symbol_info_defaults_and_fields() -> None:
    """Verify SymbolInfo default values and field assignment."""
    info = SymbolInfo(name="EURUSD", digits=5, point=0.00001)
    assert info.name == "EURUSD"
    assert info.digits == 5
    assert info.point == 0.00001
    assert info.trade_contract_size == 100_000.0
    assert info.trade_tick_size == 0.00001
    assert info.select is True
    assert info.visible is True


def test_symbol_info_round_to_tick_size() -> None:
    """Verify SymbolInfo.round_to_tick_size rounding behavior."""
    sym = SymbolInfo(name="EURUSD", digits=5, point=0.00001, trade_tick_size=0.00005)
    assert sym.round_to_tick_size(1.08542) == 1.08540
    assert sym.round_to_tick_size(1.08543) == 1.08545

    # Test fallback when trade_tick_size is 0
    sym_zero = SymbolInfo(name="TEST", digits=2, point=0.01, trade_tick_size=0.0)
    assert sym_zero.round_to_tick_size(10.556) == 10.56


def test_account_info_defaults() -> None:
    """Verify AccountInfo field defaults and initialization."""
    acc = AccountInfo(login=12345, balance=5000.0, equity=5200.0)
    assert acc.login == 12345
    assert acc.balance == 5000.0
    assert acc.equity == 5200.0
    assert acc.leverage == 100
    assert acc.currency == "USD"
    assert acc.trade_mode == AccountTradeMode.DEMO
    assert acc.margin_mode == MarginMode.RETAIL_HEDGING


def test_terminal_info_defaults() -> None:
    """Verify TerminalInfo field defaults and initialization."""
    term = TerminalInfo(connected=True, trade_allowed=True)
    assert term.connected is True
    assert term.trade_allowed is True
    assert term.name == "HaruQuantAI Simulator"
    assert term.community_account is False


def test_position_info_defaults() -> None:
    """Verify PositionInfo field defaults and initialization."""
    pos = PositionInfo(
        ticket=1001,
        identifier=1001,
        symbol="EURUSD",
        position_type=int(PositionType.BUY),
        volume=1.0,
        price_open=1.08500,
    )
    assert pos.ticket == 1001
    assert pos.identifier == 1001
    assert pos.symbol == "EURUSD"
    assert pos.volume == 1.0
    assert pos.sl == 0.0
    assert pos.tp == 0.0
    assert pos.position_type == int(PositionType.BUY)


def test_order_info_defaults() -> None:
    """Verify OrderInfo field defaults and initialization."""
    order = OrderInfo(
        ticket=2001,
        symbol="EURUSD",
        order_type=int(OrderType.BUY_LIMIT),
        volume_initial=1.0,
        volume_current=1.0,
        price_open=1.08000,
    )
    assert order.ticket == 2001
    assert order.symbol == "EURUSD"
    assert order.order_type == int(OrderType.BUY_LIMIT)
    assert order.state == int(OrderState.STARTED)


def test_deal_info_defaults() -> None:
    """Verify DealInfo field defaults and initialization."""
    deal = DealInfo(
        ticket=3001,
        order=2001,
        position_id=1001,
        symbol="EURUSD",
        deal_type=int(DealType.BUY),
        entry=int(DealEntry.IN),
        volume=1.0,
        price=1.08500,
    )
    assert deal.ticket == 3001
    assert deal.order == 2001
    assert deal.position_id == 1001
    assert deal.symbol == "EURUSD"
    assert deal.deal_type == int(DealType.BUY)


def test_book_info_defaults() -> None:
    """Verify BookInfo initialization."""
    book = BookInfo(
        type=BookType.BOOK_TYPE_BUY, price=1.08550, volume=10, volume_real=10.0
    )
    assert book.type == BookType.BOOK_TYPE_BUY
    assert book.price == 1.08550
    assert book.volume == 10
    assert book.volume_real == 10.0


def test_trade_contracts() -> None:
    """Verify TradeRequest, TradeResult, TradeCheckResult."""
    req = TradeRequest(action=TradeAction.DEAL, symbol="EURUSD", volume=0.1)
    assert req.action == TradeAction.DEAL
    assert req.symbol == "EURUSD"
    assert req.volume == 0.1

    res = TradeResult(retcode=int(TradeRetcode.DONE), deal=101, order=202)
    assert res.retcode == int(TradeRetcode.DONE)
    assert res.deal == 101
    assert res.order == 202

    check = TradeCheckResult(retcode=int(TradeRetcode.DONE), margin=100.0)
    assert check.retcode == int(TradeRetcode.DONE)
    assert check.margin == 100.0


def test_zero_shims_invariant() -> None:
    """Verify strict absence of legacy compatibility shims."""
    legacy_shims = [
        "MqlBookInfo",
        "SymbolSpec",
        "HistoryOrderSnapshot",
        "SymbolSnapshot",
        "AccountSnapshot",
        "TerminalSnapshot",
        "PositionSnapshot",
        "OrderSnapshot",
        "DealSnapshot",
    ]
    for shim in legacy_shims:
        assert not hasattr(contracts, shim), (
            f"Forbidden shim found in contracts: {shim}"
        )
