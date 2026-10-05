"""Comprehensive test suite for the broker-neutral abstraction layer with MT5.

Tests all 27 standard functions against live Pepperstone MetaTrader 5 demo
and validates capability checks against data-only brokers (Yahoo).
Credentials default to `settings.config_metatrader5`.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from app.host.logging import get_logger
from app.plugin.broker import (
    OrderAction,
    OrderType,
    TimeFrame,
    TradeRequest,
    calculate_margin,
    calculate_profit,
    check_order,
    connect,
    disconnect,
    enable_symbol,
    get_account_info,
    get_bars,
    get_history_deal_info,
    get_history_order_info,
    get_last_error,
    get_market_depth,
    get_num_history_deals,
    get_num_history_orders,
    get_num_of_symbols,
    get_num_orders,
    get_num_positions,
    get_order_info,
    get_position_info,
    get_symbol_info,
    get_symbol_tick,
    get_symbols,
    get_terminal_info,
    get_ticks,
    is_connected,
    mt5,
    subscribe_market_depth,
    trade,
    unsubscribe_market_depth,
    yahoo,
)

logger = get_logger("TestBrokerMT5")
TEST_SYMBOL = "EURUSD"


def _header(title: str) -> None:
    """Print a bounded example heading."""
    print(f"\n\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def run_all_tests() -> bool:

    _header("STARTING COMPREHENSIVE BROKER ABSTRACTION LAYER TESTS (MT5)")

    _header("1. Connect (defaults to settings.config_metatrader5)")
    response = connect(broker=mt5)
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("2. is_connected")
    response = is_connected(broker=mt5)
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("3. get_last_error")
    response = get_last_error(broker=mt5)
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("4. get_terminal_info")
    response = get_terminal_info(broker=mt5)
    assert response.is_success
    assert response.data is not None
    print(f"Message: {response.message}")
    print(f"Data: {response.data.name}")

    _header("5. get_account_info")
    response = get_account_info(broker=mt5)
    assert response.is_success
    assert response.data is not None
    print(f"Message: {response.message}")
    print(
        f"Account Balance: {response.data.balance} {response.data.currency}, Leverage: 1:{response.data.leverage}"
    )

    _header("6. get_num_of_symbols")
    response = get_num_of_symbols(broker=mt5)
    assert response.is_success
    assert response.data is not None
    assert response.data > 0
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("7. get_symbols")
    response = get_symbols(broker=mt5, group="*EURUSD*")
    assert response.is_success
    assert response.data is not None
    assert len(response.data) > 0
    print(f"Message: {response.message}")
    first_sym = response.data[0]
    print(
        f"Symbol: {first_sym.name}, Digits: {first_sym.digits}, Point: {first_sym.point}, Spread: {first_sym.spread}"
    )

    _header("8. enable_symbol")
    response = enable_symbol(broker=mt5, symbol=TEST_SYMBOL, enable=True)
    assert response.is_success
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("9. get_symbol_info")
    response = get_symbol_info(broker=mt5, symbol=TEST_SYMBOL)
    assert response.is_success
    assert response.data is not None
    sym = response.data
    print(f"Message: {response.message}")
    print(
        f"Digits: {sym.digits}, Point: {sym.point}, Spread: {sym.spread}, FillingMode: {sym.filling_mode}"
    )

    _header("10. get_symbol_tick")
    response = get_symbol_tick(broker=mt5, symbol=TEST_SYMBOL)
    assert response.is_success
    assert response.data is not None
    tick = response.data
    print(f"Message: {response.message}")
    print(f"Data: {tick.bid}, {tick.ask}, {tick.time}")

    _header("11. subscribe_market_depth")
    response = subscribe_market_depth(broker=mt5, symbol=TEST_SYMBOL)
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("12. get_market_depth")
    response = get_market_depth(broker=mt5, symbol=TEST_SYMBOL)
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("13. unsubscribe_market_depth")
    response = unsubscribe_market_depth(broker=mt5, symbol=TEST_SYMBOL)
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("14. get_bars")
    response = get_bars(
        broker=mt5, symbol=TEST_SYMBOL, timeframe=TimeFrame.H1, count=10
    )
    assert response.is_success
    assert response.data is not None
    assert len(response.data) == 10
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("15. get_ticks")
    response = get_ticks(broker=mt5, symbol=TEST_SYMBOL, count=10)
    assert response.is_success
    assert response.data is not None
    assert len(response.data) == 10
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("16. calculate_margin")
    response = calculate_margin(
        broker=mt5,
        action=OrderType.BUY,
        symbol=TEST_SYMBOL,
        volume=0.01,
        price=tick.ask,
    )
    assert response.is_success
    assert response.data is not None
    assert response.data > 0
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("17. calculate_profit")
    response = calculate_profit(
        broker=mt5,
        action=OrderType.BUY,
        symbol=TEST_SYMBOL,
        volume=0.01,
        price_open=1.1200,
        price_close=1.1250,
    )
    assert response.is_success
    assert response.data is not None
    assert response.data > 0
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("18. check_order")
    check_req = TradeRequest(
        action=OrderAction.DEAL,
        symbol=TEST_SYMBOL,
        volume=0.01,
        type=OrderType.BUY,
        price=tick.ask,
        comment="test pre-check",
    )
    response = check_order(broker=mt5, request=check_req)
    assert response.is_success
    assert response.data is not None
    assert response.data.retcode == 0
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("19. trade (send BUY deal)")
    buy_req = TradeRequest(
        action=OrderAction.DEAL,
        symbol=TEST_SYMBOL,
        volume=0.01,
        type=OrderType.BUY,
        price=tick.ask,
        comment="test buy open",
    )
    response = trade(broker=mt5, request=buy_req)
    assert response.is_success
    assert response.data is not None
    opened_order_ticket = response.data.order
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")
    print(f"Opened Order Ticket: {opened_order_ticket}")

    _header("20. get_position_info")
    response = get_position_info(broker=mt5, symbol=TEST_SYMBOL)
    assert response.is_success
    assert response.data is not None
    assert len(response.data) > 0
    active_position = None
    for p in response.data:
        if p.ticket == opened_order_ticket:
            active_position = p
            break
    if not active_position:
        active_position = response.data[0]
    print(f"Message: {response.message}")
    print(f"Data: ticket={active_position.ticket}, volume={active_position.volume}")

    _header("21. get_num_positions")
    response = get_num_positions(broker=mt5)
    assert response.is_success
    assert response.data is not None
    assert response.data > 0
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("Close opened position via counter trade")
    res_cur_tick = get_symbol_tick(broker=mt5, symbol=TEST_SYMBOL)
    assert res_cur_tick.is_success
    assert res_cur_tick.data is not None
    cur_tick = res_cur_tick.data
    close_req = TradeRequest(
        action=OrderAction.DEAL,
        symbol=TEST_SYMBOL,
        volume=active_position.volume,
        type=OrderType.SELL,
        position=active_position.ticket,
        price=cur_tick.bid,
        comment="test close position",
    )
    response = trade(broker=mt5, request=close_req)
    assert response.is_success
    assert response.data is not None
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("22. get_order_info (active pending orders)")
    response = get_order_info(broker=mt5)
    assert response.is_success
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("23. get_num_orders")
    response = get_num_orders(broker=mt5)
    assert response.is_success
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("24. get_history_order_info")
    response = get_history_order_info(broker=mt5)
    assert response.is_success
    assert response.data is not None
    assert len(response.data) > 0
    print(f"Message: {response.message}")
    print(f"Data (count): {len(response.data)}")

    _header("25. get_num_history_orders")
    response = get_num_history_orders(broker=mt5)
    assert response.is_success
    assert response.data is not None
    assert response.data > 0
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("26. get_history_deal_info")
    response = get_history_deal_info(broker=mt5)
    assert response.is_success
    assert response.data is not None
    assert len(response.data) > 0
    print(f"Message: {response.message}")
    print(f"Data (count): {len(response.data)}")

    _header("27. get_num_history_deals")
    response = get_num_history_deals(broker=mt5)
    assert response.is_success
    assert response.data is not None
    assert response.data > 0
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("28. Test Non-Trading Broker Capability (Yahoo)")
    yahoo_trade_req = TradeRequest(symbol="AAPL", volume=1.0, type=OrderType.BUY)
    response = trade(broker=yahoo, request=yahoo_trade_req)
    assert not response.is_success, "Yahoo trading should fail"
    assert "doesn't have trading capabilities" in response.message
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("29. get_bars(broker='yahoo', symbol='AAPL')")
    response = get_bars(broker="yahoo", symbol="AAPL", count=1)
    assert response.is_success
    assert response.data is not None
    assert len(response.data) == 1
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("30. Disconnect")
    response = disconnect(broker=mt5)
    assert response.is_success
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    _header("31. is_connected (after disconnect)")
    response = is_connected(broker=mt5)
    assert response.is_success
    assert response.data is False
    print(f"Message: {response.message}")
    print(f"Data: {response.data}")

    print("\n" + "=" * 80)
    print("ALL 27 BROKER-NEUTRAL FUNCTIONS AND CAPABILITY CHECKS PASSED SUCCESSFULLY!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
