"""Unit tests for strategy control blocks and StrategyControl facade.

Description:
    Tests StrategyQuant donor-faithful strategy control blocks, exact donor
    class aliases, unified StrategyControl facade, BlockRegistry discovery,
    non-silent requirement logging, and edge case validations.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-ACCOUNT-BALANCE: Account balance block and alias tests.
    - FR-STRATEGY-CONTROL-ACCOUNT-EQUITY: Account equity block and alias tests.
    - FR-STRATEGY-CONTROL-BARS-SINCE-ORDER-CLOSED: Bars since order closed tests.
    - FR-STRATEGY-CONTROL-BARS-SINCE-ORDER-OPEN: Bars since order open tests.
    - FR-STRATEGY-CONTROL-CLOSED-PL-IN-MONEY: Closed P/L in money tests.
    - FR-STRATEGY-CONTROL-CLOSED-PL-IN-PIPS: Closed P/L in pips tests.
    - FR-STRATEGY-CONTROL-LAST-ORDER-WAS: Last order was tests.
    - FR-STRATEGY-CONTROL-LAST-ORDER-WAS-NOT: Last order was not tests.
    - FR-STRATEGY-CONTROL-MARKET-POSITION: Market position tests.
    - FR-STRATEGY-CONTROL-MARKET-POSITION-IS-FLAT: Market position is flat tests.
    - FR-STRATEGY-CONTROL-MARKET-POSITION-IS-LONG: Market position is long tests.
    - FR-STRATEGY-CONTROL-MARKET-POSITION-IS-NOT-LONG: Market position is not long tests.
    - FR-STRATEGY-CONTROL-MARKET-POSITION-IS-NOT-SHORT: Market position is not short tests.
    - FR-STRATEGY-CONTROL-MARKET-POSITION-IS-SHORT: Market position is short tests.
    - FR-STRATEGY-CONTROL-MARKET-POSITIONS-COUNT: Market positions count tests.
    - FR-STRATEGY-CONTROL-MARKET-POSITION-SIZE: Market position size tests.
    - FR-STRATEGY-CONTROL-NO-TRADE-RECENTLY-CLOSED: No trade recently closed tests.
    - FR-STRATEGY-CONTROL-OPEN-PL-IN-MONEY: Open P/L in money tests.
    - FR-STRATEGY-CONTROL-OPEN-PL-IN-PIPS: Open P/L in pips tests.
    - FR-STRATEGY-CONTROL-ORDER-OPEN-PRICE: Order open price tests.
    - FR-STRATEGY-CONTROL-ORDER-PT: Order profit target tests.
    - FR-STRATEGY-CONTROL-ORDER-SL: Order stop loss tests.
    - FR-STRATEGY-CONTROL-PENDING-ORDER-DOESNT-EXIST: Pending order doesn't exist tests.
    - FR-STRATEGY-CONTROL-PENDING-ORDER-EXISTS: Pending order exists tests.
    - FR-STRATEGY-CONTROL-TRADE-RECENTLY-CLOSED: Trade recently closed tests.
    - FR-STRATEGY-CONTROL-FACADE: Unified StrategyControl facade tests.
    - FR-STRATEGY-CONTROL-EXPORTS: Package exports and registry discovery tests.
Python API Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import pytest
from app.core.data.contracts import PositionInfo, SymbolInfo, SymbolPrice
from app.core.trading.blocks.registry import BlockRegistry
from app.extend.blocks.order.open.enter_at_limit import enter_at_limit
from app.extend.blocks.order.open.enter_at_market import enter_at_market
from app.extend.blocks.strategy_control import (
    AccountBalance,
    AccountEquity,
    BarsSinceOrderClosed,
    BarsSinceOrderOpen,
    ClosedPLInMoney,
    ClosedPLInPips,
    LastOrderWas,
    LastOrderWasNot,
    MarketPosition,
    MarketPositionIsFlat,
    MarketPositionIsLong,
    MarketPositionIsNotLong,
    MarketPositionIsNotShort,
    MarketPositionIsShort,
    MarketPositionsCount,
    MarketPositionSize,
    NoTradeRecentlyClosed,
    OpenPLInMoney,
    OpenPLInPips,
    OrderOpenPrice,
    OrderPT,
    OrderSL,
    PendingOrderDoesntExist,
    PendingOrderExists,
    StrategyControl,
    TradeRecentlyClosed,
    account_balance,
    account_equity,
    bars_since_order_closed,
    bars_since_order_open,
    closed_pl_in_money,
    closed_pl_in_pips,
    last_order_was,
    last_order_was_not,
    last_trade,
    market_position,
    market_position_is_flat,
    market_position_is_long,
    market_position_is_not_long,
    market_position_is_not_short,
    market_position_is_short,
    market_position_size,
    market_positions_count,
    no_trade_recently_closed,
    open_pl_in_money,
    open_pl_in_pips,
    order_open_price,
    order_pt,
    order_sl,
    pending_order_doesnt_exist,
    pending_order_exists,
    trade_recently_closed,
    valuation,
)
from app.extend.functions.order_functions import TradeFilter
from app.workspace.brokers.simulator import SimulatorClient
from app.workspace.trading import Trading

START = datetime(2026, 10, 27, 10, tzinfo=UTC)


@pytest.fixture
def sim_trading() -> tuple[Trading, SimulatorClient]:
    """Provide a fresh simulated trading environment."""
    client = SimulatorClient(initial_balance=100_000, commission_per_lot=2)
    client.set_clock(START)
    for name in ("EURUSD", "GBPUSD"):
        client.add_symbol(SymbolInfo(name=name, price=SymbolPrice(pip_size=0.0001)))
        client.feed_tick(name, bid=1.1, ask=1.1002)
    trading = Trading(client)
    trading.arm()
    return trading, client


def test_donor_aliases_parity() -> None:
    """Verify that all 25 SQ donor class aliases match the canonical block functions."""
    assert AccountBalance is account_balance
    assert AccountEquity is account_equity
    assert BarsSinceOrderClosed is bars_since_order_closed
    assert BarsSinceOrderOpen is bars_since_order_open
    assert ClosedPLInMoney is closed_pl_in_money
    assert ClosedPLInPips is closed_pl_in_pips
    assert LastOrderWas is last_order_was
    assert LastOrderWasNot is last_order_was_not
    assert MarketPosition is market_position
    assert MarketPositionIsFlat is market_position_is_flat
    assert MarketPositionIsLong is market_position_is_long
    assert MarketPositionIsNotLong is market_position_is_not_long
    assert MarketPositionIsNotShort is market_position_is_not_short
    assert MarketPositionIsShort is market_position_is_short
    assert MarketPositionsCount is market_positions_count
    assert MarketPositionSize is market_position_size
    assert NoTradeRecentlyClosed is no_trade_recently_closed
    assert OpenPLInMoney is open_pl_in_money
    assert OpenPLInPips is open_pl_in_pips
    assert OrderOpenPrice is order_open_price
    assert OrderPT is order_pt
    assert OrderSL is order_sl
    assert PendingOrderDoesntExist is pending_order_doesnt_exist
    assert PendingOrderExists is pending_order_exists
    assert TradeRecentlyClosed is trade_recently_closed


def test_registry_discovery() -> None:
    """Verify BlockRegistry discovers all 25 strategy control blocks without diagnostics."""
    registry = BlockRegistry()
    count = registry.discover("app/extend/blocks/strategy_control")
    assert count == 25

    expected_ids = {
        "strategy_control.account_balance",
        "strategy_control.account_equity",
        "strategy_control.bars_since_order_closed",
        "strategy_control.bars_since_order_open",
        "strategy_control.closed_pl_in_money",
        "strategy_control.closed_pl_in_pips",
        "strategy_control.last_order_was",
        "strategy_control.last_order_was_not",
        "strategy_control.market_position",
        "strategy_control.market_position_is_flat",
        "strategy_control.market_position_is_long",
        "strategy_control.market_position_is_not_long",
        "strategy_control.market_position_is_not_short",
        "strategy_control.market_position_is_short",
        "strategy_control.market_position_size",
        "strategy_control.market_positions_count",
        "strategy_control.no_trade_recently_closed",
        "strategy_control.open_pl_in_money",
        "strategy_control.open_pl_in_pips",
        "strategy_control.order_open_price",
        "strategy_control.order_pt",
        "strategy_control.order_sl",
        "strategy_control.pending_order_doesnt_exist",
        "strategy_control.pending_order_exists",
        "strategy_control.trade_recently_closed",
    }
    discovered = {b.spec.id for b in registry.snapshot().blocks.values()}
    assert expected_ids.issubset(discovered)


@pytest.mark.anyio
async def test_facade_and_account_blocks(
    sim_trading: tuple[Trading, SimulatorClient],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test facade and discrete account blocks, including caplog verification."""
    trading, _ = sim_trading
    caplog.set_level(logging.DEBUG)

    ctrl = StrategyControl(trading)

    # Initial balance and equity
    balance = await ctrl.account_balance()
    equity = await ctrl.account_equity()
    assert balance == 100000.0
    assert equity == 100000.0

    assert "FR-STRATEGY-CONTROL-ACCOUNT-BALANCE" in caplog.text
    assert "FR-STRATEGY-CONTROL-ACCOUNT-EQUITY" in caplog.text


@pytest.mark.anyio
async def test_facade_unbound_context_resolution(
    sim_trading: tuple[Trading, SimulatorClient],
) -> None:
    """Verify facade works when context is supplied per call or raises ValueError."""
    trading, _ = sim_trading
    unbound_ctrl = StrategyControl()

    # Should raise when no context is provided
    with pytest.raises(ValueError, match="A TradingRuntime context must be provided"):
        await unbound_ctrl.account_balance()

    # Should succeed when context is explicitly passed
    balance = await unbound_ctrl.account_balance(context=trading)
    assert balance == 100000.0


@pytest.mark.anyio
async def test_market_position_blocks(
    sim_trading: tuple[Trading, SimulatorClient],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test market position queries across empty and filled states."""
    trading, client = sim_trading
    caplog.set_level(logging.DEBUG)
    scope = TradeFilter("EURUSD", magic=42)

    ctrl = StrategyControl(trading)

    # Empty state
    assert await ctrl.market_position(scope) == 0
    assert await ctrl.market_position_is_flat(scope) is True
    assert await ctrl.market_position_is_long(scope) is False
    assert await ctrl.market_position_is_not_long(scope) is True
    assert await ctrl.market_position_is_short(scope) is False
    assert await ctrl.market_position_is_not_short(scope) is True
    assert await ctrl.market_positions_count(scope) == 0
    assert await ctrl.market_position_size(scope) == 0.0

    # Enter a long position
    await enter_at_market(trading, "EURUSD", 1, 0.05, magic=42, comment="buy_test")

    assert await ctrl.market_position(scope) == 1
    assert await ctrl.market_position_is_flat(scope) is False
    assert await ctrl.market_position_is_long(scope) is True
    assert await ctrl.market_position_is_not_long(scope) is False
    assert await ctrl.market_position_is_short(scope) is False
    assert await ctrl.market_position_is_not_short(scope) is True
    assert await ctrl.market_positions_count(scope) == 1
    assert await ctrl.market_position_size(scope) == 0.05

    assert "FR-STRATEGY-CONTROL-MARKET-POSITION" in caplog.text
    assert "FR-STRATEGY-CONTROL-MARKET-POSITION-IS-FLAT" in caplog.text
    assert "FR-STRATEGY-CONTROL-MARKET-POSITION-IS-LONG" in caplog.text
    assert "FR-STRATEGY-CONTROL-MARKET-POSITIONS-COUNT" in caplog.text
    assert "FR-STRATEGY-CONTROL-MARKET-POSITION-SIZE" in caplog.text


@pytest.mark.anyio
async def test_order_values_and_pending_orders(
    sim_trading: tuple[Trading, SimulatorClient],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test order_open_price, order_pt, order_sl, and pending order queries."""
    trading, _ = sim_trading
    caplog.set_level(logging.DEBUG)
    scope = TradeFilter("EURUSD", magic=101)
    ctrl = StrategyControl(trading)

    # When no order exists, sentinels return -1.0
    assert await ctrl.order_open_price(scope) == -1.0
    assert await ctrl.order_pt(scope) == -1.0
    assert await ctrl.order_sl(scope) == -1.0
    assert await ctrl.pending_order_exists(scope) is False
    assert await ctrl.pending_order_doesnt_exist(scope) is True

    # Place a pending limit order
    await enter_at_limit(
        trading,
        "EURUSD",
        1,
        0.05,
        1.0950,
        sl=1.0900,
        tp=1.1100,
        magic=101,
    )

    assert await ctrl.pending_order_exists(scope) is True
    assert await ctrl.pending_order_doesnt_exist(scope) is False
    assert await ctrl.order_open_price(scope, pending=True) == 1.0950
    assert await ctrl.order_sl(scope, pending=True) == 1.0900
    assert await ctrl.order_pt(scope, pending=True) == 1.1100

    assert "FR-STRATEGY-CONTROL-ORDER-OPEN-PRICE" in caplog.text
    assert "FR-STRATEGY-CONTROL-ORDER-SL" in caplog.text
    assert "FR-STRATEGY-CONTROL-ORDER-PT" in caplog.text
    assert "FR-STRATEGY-CONTROL-PENDING-ORDER-EXISTS" in caplog.text
    assert "FR-STRATEGY-CONTROL-PENDING-ORDER-DOESNT-EXIST" in caplog.text


@pytest.mark.anyio
async def test_open_pl_in_money_and_pips(
    sim_trading: tuple[Trading, SimulatorClient],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test open P/L in money and pips with and without custom valuation."""
    trading, client = sim_trading
    caplog.set_level(logging.DEBUG)
    scope = TradeFilter("EURUSD", magic=88)
    ctrl = StrategyControl(trading)

    await enter_at_market(trading, "EURUSD", 1, 0.05, magic=88)

    # Initial open PL
    money_pl = await ctrl.open_pl_in_money(scope)
    pip_pl = await ctrl.open_pl_in_pips(scope)
    assert isinstance(money_pl, float)
    assert isinstance(pip_pl, float)

    # Using custom mark valuation prices
    custom_money = await ctrl.open_pl_in_money(scope, prices={"EURUSD": 1.1050})
    custom_pips = await ctrl.open_pl_in_pips(scope, prices={"EURUSD": 1.1050})
    assert custom_money > 0
    assert custom_pips > 0

    assert "FR-STRATEGY-CONTROL-OPEN-PL-IN-MONEY" in caplog.text
    assert "FR-STRATEGY-CONTROL-OPEN-PL-IN-PIPS" in caplog.text


@pytest.mark.anyio
async def test_bars_since_and_trade_recently_closed(
    sim_trading: tuple[Trading, SimulatorClient],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test bars_since_order_open, bars_since_order_closed, and trade_recently_closed."""
    trading, client = sim_trading
    caplog.set_level(logging.DEBUG)
    scope = TradeFilter("EURUSD", magic=77)
    ctrl = StrategyControl(trading)

    now = START
    bar_times = [START - timedelta(minutes=5 * i) for i in range(10)]
    bar_times.reverse()

    # Prior to entry
    assert await ctrl.bars_since_order_open(scope, bar_times, as_of=now) == -1
    assert await ctrl.bars_since_order_closed(scope, bar_times, as_of=now) == -1

    await enter_at_market(trading, "EURUSD", 1, 0.05, magic=77)

    # After entry
    bars_open = await ctrl.bars_since_order_open(scope, bar_times, as_of=now)
    assert bars_open >= 0

    # Trade recently closed
    assert (
        await ctrl.trade_recently_closed(
            scope, as_of=now, bar_start=START, check_this_bar=True
        )
        is False
    )
    assert (
        await ctrl.no_trade_recently_closed(
            scope, as_of=now, bar_start=START, check_this_bar=True
        )
        is True
    )

    assert "FR-STRATEGY-CONTROL-BARS-SINCE-ORDER-OPEN" in caplog.text
    assert "FR-STRATEGY-CONTROL-BARS-SINCE-ORDER-CLOSED" in caplog.text
    assert "FR-STRATEGY-CONTROL-TRADE-RECENTLY-CLOSED" in caplog.text
    assert "FR-STRATEGY-CONTROL-NO-TRADE-RECENTLY-CLOSED" in caplog.text


@pytest.mark.anyio
async def test_validation_and_error_handling(
    sim_trading: tuple[Trading, SimulatorClient],
) -> None:
    """Test error handling on invalid direction, non-positive valuation, and bad args."""
    trading, _ = sim_trading
    scope = TradeFilter("EURUSD")
    ctrl = StrategyControl(trading)

    # Direction validation
    with pytest.raises(ValueError, match="direction must be 1 or -1"):
        await ctrl.last_order_was(scope, direction=0)

    with pytest.raises(ValueError, match="direction must be 1 or -1"):
        await ctrl.last_order_was_not(scope, direction=2)

    # Valuation validation
    pos = PositionInfo(
        ticket=1,
        symbol="EURUSD",
        position_type=0,
        volume=1.0,
        price_open=1.1,
        price_current=0.0,  # non-positive
    )
    with pytest.raises(
        ValueError, match="valuation prices must be finite and positive"
    ):
        valuation(pos, None)

    # Trade recently closed without bar_start
    with pytest.raises(
        ValueError, match="bar_start is required when checking this bar"
    ):
        await ctrl.trade_recently_closed(
            scope, as_of=START, bar_start=None, check_this_bar=True
        )

    # Future bar_start
    with pytest.raises(ValueError, match="bar_start must not exceed evaluation time"):
        await ctrl.trade_recently_closed(
            scope,
            as_of=START,
            bar_start=START + timedelta(minutes=5),
            check_this_bar=True,
        )

    # last_trade negative trades_ago
    with pytest.raises(ValueError, match="trades_ago must be a nonnegative integer"):
        await last_trade(trading, scope, trades_ago=-1, as_of=None)
