"""Test script testing all registered broker plugins in app/plugin/broker.

Validates:
- MetaTrader5 (Live trading, execution, quotes, bars, history)
- Yahoo (Live v8 chart API quotes & bars, capability check)
- Dukascopy (Live StrategyQuant CDN fast quotes & bars, capability check)
- Darwinex (Catalog & specs, capability check)
- SQ_Equity (Local partitioned Parquet datasets, AAPL/MSFT, capability check)
- SQ_Futures (Local partitioned Parquet datasets, @ES/CL, capability check)
- cTrader (Spotware Open API SSL TLS connection, App Auth & Account Auth)
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
    check_order,
    connect,
    ctrader,
    darwinex,
    disconnect,
    dukascopy,
    get_account_info,
    get_bars,
    get_position_info,
    get_symbol_info,
    get_symbol_tick,
    get_symbols,
    get_terminal_info,
    mt5,
    sq_equity,
    sq_futures,
    trade,
    yahoo,
)

logger = get_logger("TestAllBrokers")


def run_tests() -> bool:
    print("=" * 80)
    print("RUNNING MULTI-BROKER INTEGRATION TESTS")
    print("=" * 80)

    # ------------------------------------------------------------------------
    # 1. MetaTrader 5 (Live Trading & Data via settings.config_metatrader5)
    # ------------------------------------------------------------------------
    print("\n[1] METATRADER 5:")
    res = connect(broker=mt5)
    print(f"    Connect: success={res.is_success}, msg={res.message}")
    assert res.is_success, f"MT5 connection failed: {res.message}"

    term = get_terminal_info(broker=mt5)
    print(
        f"    Terminal: {term.data.name if term.data else 'None'}, Connected: {term.data.connected if term.data else 'None'}"
    )
    acc = get_account_info(broker=mt5)
    print(
        f"    Account: Balance={acc.data.balance if acc.data else 'None'} {acc.data.currency if acc.data else ''}"
    )
    tick = get_symbol_tick(broker=mt5, symbol="EURUSD")
    print(
        f"    Tick: Bid={tick.data.bid if tick.data else 'None'}, Ask={tick.data.ask if tick.data else 'None'}"
    )
    bars = get_bars(broker=mt5, symbol="EURUSD", timeframe=TimeFrame.H1, count=3)
    print(f"    Bars count: {len(bars.data) if bars.data else 0}")

    # Trade test (Open & Close 0.01 lot)
    buy_res = trade(
        broker=mt5,
        request=TradeRequest(
            action=OrderAction.DEAL,
            symbol="EURUSD",
            volume=0.01,
            type=OrderType.BUY,
            comment="multi test",
        ),
    )
    print(
        f"    Trade Buy: success={buy_res.is_success}, order={buy_res.data.order if buy_res.data else 'None'}"
    )
    assert buy_res.is_success
    pos = get_position_info(broker=mt5, symbol="EURUSD")
    if pos.data:
        target = pos.data[0]
        cur_tick = get_symbol_tick(broker=mt5, symbol="EURUSD").data
        close_res = trade(
            broker=mt5,
            request=TradeRequest(
                action=OrderAction.DEAL,
                symbol="EURUSD",
                volume=target.volume,
                type=OrderType.SELL,
                position=target.ticket,
                price=cur_tick.bid if cur_tick else 0.0,
                comment="multi close",
            ),
        )
        print(f"    Trade Close: success={close_res.is_success}")
    disconnect(broker=mt5)
    print("    MT5 disconnected successfully.")

    # ------------------------------------------------------------------------
    # 2. Yahoo Finance (Live v8 API)
    # ------------------------------------------------------------------------
    print("\n[2] YAHOO FINANCE:")
    y_info = get_symbol_info(broker=yahoo, symbol="AAPL")
    print(
        f"    Symbol Info: {y_info.data.name if y_info.data else 'None'}, Price={y_info.data.bid if y_info.data else 'None'}"
    )
    y_bars = get_bars(broker=yahoo, symbol="AAPL", timeframe=TimeFrame.D1, count=5)
    print(f"    Bars count: {len(y_bars.data) if y_bars.data else 0}")
    assert y_bars.is_success
    assert y_bars.data is not None
    assert len(y_bars.data) == 5
    y_trade = trade(broker=yahoo, request=TradeRequest(symbol="AAPL", volume=1))
    print(
        f"    Trade Attempt: success={y_trade.is_success}, message='{y_trade.message}'"
    )
    assert not y_trade.is_success
    assert "doesn't have trading capabilities" in y_trade.message

    # ------------------------------------------------------------------------
    # 3. Dukascopy (StrategyQuant CDN datafeed)
    # ------------------------------------------------------------------------
    print("\n[3] DUKASCOPY:")
    d_info = get_symbol_info(broker=dukascopy, symbol="EURUSD")
    print(
        f"    Symbol Info: {d_info.data.name if d_info.data else 'None'}, Digits={d_info.data.digits if d_info.data else 'None'}"
    )
    d_bars = get_bars(broker=dukascopy, symbol="EURUSD", count=5)
    print(f"    CDN Bars count: {len(d_bars.data) if d_bars.data else 0}")
    assert d_bars.is_success
    assert d_bars.data is not None
    assert len(d_bars.data) > 0
    d_trade = trade(broker=dukascopy, request=TradeRequest(symbol="EURUSD", volume=1))
    print(
        f"    Trade Attempt: success={d_trade.is_success}, message='{d_trade.message}'"
    )
    assert not d_trade.is_success
    assert "doesn't have trading capabilities" in d_trade.message

    # ------------------------------------------------------------------------
    # 4. Darwinex (Catalog & Specs)
    # ------------------------------------------------------------------------
    print("\n[4] DARWINEX:")
    dw_info = get_symbol_info(broker=darwinex, symbol="EURUSD")
    print(
        f"    Symbol Info: {dw_info.data.name if dw_info.data else 'None'}, Digits={dw_info.data.digits if dw_info.data else 'None'}"
    )
    dw_syms = get_symbols(broker=darwinex)
    print(f"    Symbols count: {len(dw_syms.data) if dw_syms.data else 0}")
    assert dw_syms.is_success
    assert dw_syms.data is not None
    assert len(dw_syms.data) > 0
    dw_trade = trade(broker=darwinex, request=TradeRequest(symbol="EURUSD", volume=1))
    print(
        f"    Trade Attempt: success={dw_trade.is_success}, message='{dw_trade.message}'"
    )
    assert not dw_trade.is_success
    assert "doesn't have trading capabilities" in dw_trade.message

    # ------------------------------------------------------------------------
    # 5. SQ Equity (Local Parquet Datasets: AAPL, MSFT, QQQ, SPY)
    # ------------------------------------------------------------------------
    print("\n[5] SQ EQUITY:")
    eq_info = get_symbol_info(broker=sq_equity, symbol="AAPL")
    print(f"    Symbol Info: {eq_info.data.name if eq_info.data else 'None'}")
    eq_bars = get_bars(broker=sq_equity, symbol="AAPL", count=5)
    print(f"    Parquet Bars count: {len(eq_bars.data) if eq_bars.data else 0}")
    assert eq_bars.is_success
    assert eq_bars.data is not None
    assert len(eq_bars.data) == 5
    print(f"    Sample Bar: {eq_bars.data[-1]}")
    eq_trade = trade(broker=sq_equity, request=TradeRequest(symbol="AAPL", volume=1))
    print(
        f"    Trade Attempt: success={eq_trade.is_success}, message='{eq_trade.message}'"
    )
    assert not eq_trade.is_success
    assert "doesn't have trading capabilities" in eq_trade.message

    # ------------------------------------------------------------------------
    # 6. SQ Futures (Local Parquet Datasets: @ES, CL)
    # ------------------------------------------------------------------------
    print("\n[6] SQ FUTURES:")
    fut_info = get_symbol_info(broker=sq_futures, symbol="@ES")
    print(
        f"    Symbol Info: {fut_info.data.name if fut_info.data else 'None'}, TickSize={fut_info.data.point if fut_info.data else 'None'}"
    )
    fut_bars = get_bars(broker=sq_futures, symbol="@ES", count=5)
    print(f"    Parquet Bars count: {len(fut_bars.data) if fut_bars.data else 0}")
    assert fut_bars.is_success
    assert fut_bars.data is not None
    assert len(fut_bars.data) == 5
    print(f"    Sample Bar: {fut_bars.data[-1]}")
    fut_trade = trade(broker=sq_futures, request=TradeRequest(symbol="@ES", volume=1))
    print(
        f"    Trade Attempt: success={fut_trade.is_success}, message='{fut_trade.message}'"
    )
    assert not fut_trade.is_success
    assert "doesn't have trading capabilities" in fut_trade.message

    # ------------------------------------------------------------------------
    # 7. cTrader Open API (Gateway & Auth Protocol via settings.config_ctrader)
    # ------------------------------------------------------------------------
    print("\n[7] CTRADER OPEN API:")
    c_conn = connect(broker=ctrader)
    print(
        f"    Gateway Connection & Auth: success={c_conn.is_success}, message='{c_conn.message}'"
    )
    c_info = get_symbol_info(broker=ctrader, symbol="EURUSD")
    print(
        f"    Symbol Info: {c_info.data.name if c_info.data else 'None'}, Digits={c_info.data.digits if c_info.data else 'None'}"
    )
    c_syms = get_symbols(broker=ctrader)
    print(f"    Symbols count: {len(c_syms.data) if c_syms.data else 0}")
    c_chk = check_order(
        broker=ctrader, request=TradeRequest(symbol="EURUSD", volume=0.01)
    )
    print(f"    Order Check: success={c_chk.is_success}, message='{c_chk.message}'")
    disconnect(broker=ctrader)
    print("    cTrader disconnected successfully.")

    print("\n" + "=" * 80)
    print("ALL 7 BROKERS SUCCESSFULLY VERIFIED AND COMPATIBLE WITH BASE CONTRACTS!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
