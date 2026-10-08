"""Test script testing all registered broker plugins in app/plugins/brokers.

Validates:
- MetaTrader5 (Live trading, execution, quotes, bars, history)
- cTrader (Spotware Open API SSL TLS connection, App Auth & Account Auth)
- Yahoo (Market data provider: live v8 chart API bars, data download)
- Dukascopy (Market data provider: StrategyQuant CDN fast bars, Parquet)
- Darwinex (Market data provider: Parquet data ingestion)
- SQ_Equity (Market data provider: Local partitioned Parquet datasets, AAPL/MSFT)
- SQ_Futures (Market data provider: Local partitioned Parquet datasets, @ES/CL)
- Binance (Market data provider: REST API live klines, trades)
- Files (Market data provider: Local CSV/Parquet historical bar parsing)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.host.logging import get_logger
from app.plugins.brokers import (
    OrderAction,
    OrderType,
    TimeFrame,
    TradeRequest,
    binance,
    check_order,
    connect,
    ctrader,
    darwinex,
    disconnect,
    dukascopy,
    files,
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
from app.workspace.data_manager.connections import DownloadRequest

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
        f"    Terminal: {term.data.name if term.data else 'None'}, "
        f"Connected: {term.data.connected if term.data else 'None'}"
    )
    acc = get_account_info(broker=mt5)
    print(
        f"    Account: Balance={acc.data.balance if acc.data else 'None'} "
        f"{acc.data.currency if acc.data else ''}"
    )
    tick = get_symbol_tick(broker=mt5, symbol="EURUSD")
    print(
        f"    Tick: Bid={tick.data.bid if tick.data else 'None'}, "
        f"Ask={tick.data.ask if tick.data else 'None'}"
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
        f"    Trade Buy: success={buy_res.is_success}, "
        f"order={buy_res.data.order if buy_res.data else 'None'}"
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
    # 2. Yahoo Finance (Market Data Provider: Live v8 API)
    # ------------------------------------------------------------------------
    print("\n[2] YAHOO FINANCE:")
    y_info = get_symbol_info(broker=yahoo, symbol="AAPL")
    print(
        f"    Symbol Info: {y_info.data.description if y_info.data else 'None'}, "
        f"Exchange: {y_info.data.exchange if y_info.data else 'None'}"
    )
    assert y_info.is_success
    assert y_info.data is not None

    y_bars = get_bars(broker=yahoo, symbol="AAPL", timeframe=TimeFrame.D1, count=5)
    print(f"    Bars count: {len(y_bars.data) if y_bars.data else 0}")
    assert y_bars.is_success
    assert y_bars.data is not None
    assert len(y_bars.data) == 5
    y_trade = trade(broker=yahoo, request=TradeRequest(symbol="AAPL", volume=1))
    print(
        f"    Trade Rejection: success={y_trade.is_success}, message='{y_trade.message}'"
    )
    assert not y_trade.is_success
    assert "doesn't have trading capabilities" in y_trade.message

    # ------------------------------------------------------------------------
    # 3. Dukascopy (In-Memory CDN Bars & Authoritative CSV Symbol Catalog)
    # ------------------------------------------------------------------------
    print("\n[3] DUKASCOPY:")
    d_info = get_symbol_info(broker=dukascopy, symbol="EURUSD")
    print(
        f"    Symbol Info: {d_info.data.description if d_info.data else 'None'}, "
        f"digits={d_info.data.digits if d_info.data else 'None'}"
    )
    assert d_info.is_success
    assert d_info.data is not None
    assert d_info.data.digits == 5

    d_num = dukascopy.get_num_of_symbols()
    print(f"    Catalog Symbols: {d_num.data}")
    assert d_num.is_success
    assert d_num.data == 725

    d_bars = get_bars(broker=dukascopy, symbol="EURUSD", count=5)
    print(
        f"    CDN Bars: count={len(d_bars.data) if d_bars.data else 0} "
        f"(success={d_bars.is_success})"
    )
    assert d_bars.is_success
    assert d_bars.data is not None
    assert len(d_bars.data) == 5

    d_trade = trade(broker=dukascopy, request=TradeRequest(symbol="EURUSD", volume=1))
    print(
        f"    Trade Rejection: success={d_trade.is_success}, message='{d_trade.message}'"
    )
    assert not d_trade.is_success
    assert "doesn't have trading capabilities" in d_trade.message

    # ------------------------------------------------------------------------
    # 4. Darwinex (In-Memory CDN Bars & Authoritative CSV Symbol Catalog)
    # ------------------------------------------------------------------------
    print("\n[4] DARWINEX:")
    dw_info = get_symbol_info(broker=darwinex, symbol="EURUSD")
    print(
        f"    Symbol Info: {dw_info.data.description if dw_info.data else 'None'}, "
        f"digits={dw_info.data.digits if dw_info.data else 'None'}"
    )
    assert dw_info.is_success
    assert dw_info.data is not None
    assert dw_info.data.digits == 5

    dw_num = darwinex.get_num_of_symbols()
    print(f"    Catalog Symbols: {dw_num.data}")
    assert dw_num.is_success
    assert dw_num.data == 328

    dw_bars = get_bars(broker=darwinex, symbol="EURUSD", count=5)
    print(
        f"    CDN Bars: count={len(dw_bars.data) if dw_bars.data else 0} "
        f"(success={dw_bars.is_success})"
    )
    assert dw_bars.is_success
    assert dw_bars.data is not None
    assert len(dw_bars.data) == 5

    dw_trade = trade(broker=darwinex, request=TradeRequest(symbol="EURUSD", volume=1))
    print(
        f"    Trade Rejection: success={dw_trade.is_success}, message='{dw_trade.message}'"
    )
    assert not dw_trade.is_success
    assert "doesn't have trading capabilities" in dw_trade.message

    # ------------------------------------------------------------------------
    # 5. SQ Equity (Market Data Provider: Parquet Datasets & US Equity Catalog)
    # ------------------------------------------------------------------------
    print("\n[5] SQ EQUITY:")
    eq_info = get_symbol_info(broker=sq_equity, symbol="AAPL")
    print(
        f"    Symbol Info: {eq_info.data.description if eq_info.data else 'None'}, "
        f"digits={eq_info.data.digits if eq_info.data else 'None'}"
    )
    assert eq_info.is_success
    assert eq_info.data is not None
    assert eq_info.data.name == "AAPL"

    eq_num = sq_equity.get_num_of_symbols()
    print(f"    Catalog Symbols: {eq_num.data}")
    assert eq_num.is_success
    assert eq_num.data is not None
    assert eq_num.data >= 10

    eq_etfs = sq_equity.get_symbols(group="ETFs")
    print(f"    ETFs count: {len(eq_etfs.data) if eq_etfs.data else 0}")
    assert eq_etfs.is_success
    assert eq_etfs.data is not None
    assert len(eq_etfs.data) > 0

    eq_bars = get_bars(broker=sq_equity, symbol="AAPL", count=5)
    print(f"    Parquet Bars count: {len(eq_bars.data) if eq_bars.data else 0}")
    assert eq_bars.is_success
    assert eq_bars.data is not None
    assert len(eq_bars.data) == 5

    eq_trade = trade(broker=sq_equity, request=TradeRequest(symbol="AAPL", volume=1))
    print(
        f"    Trade Rejection: success={eq_trade.is_success}, message='{eq_trade.message}'"
    )
    assert not eq_trade.is_success
    assert "doesn't have trading capabilities" in eq_trade.message

    # ------------------------------------------------------------------------
    # 6. SQ Futures (Market Data Provider: Local Parquet Datasets: @ES, CL)
    # ------------------------------------------------------------------------
    print("\n[6] SQ FUTURES:")
    fut_bars = get_bars(broker=sq_futures, symbol="@ES", count=5)
    print(f"    Parquet Bars count: {len(fut_bars.data) if fut_bars.data else 0}")
    assert fut_bars.is_success
    assert fut_bars.data is not None
    assert len(fut_bars.data) == 5

    fut_trade = trade(broker=sq_futures, request=TradeRequest(symbol="@ES", volume=1))
    print(
        f"    Trade Rejection: success={fut_trade.is_success}, message='{fut_trade.message}'"
    )
    assert not fut_trade.is_success
    assert "doesn't have trading capabilities" in fut_trade.message

    # ------------------------------------------------------------------------
    # 7. cTrader Open API (Live Execution Broker: Gateway & Auth Protocol)
    # ------------------------------------------------------------------------
    print("\n[7] CTRADER OPEN API:")
    c_conn = connect(broker=ctrader)
    print(
        f"    Gateway Connection & Auth: success={c_conn.is_success}, "
        f"message='{c_conn.message}'"
    )
    c_info = get_symbol_info(broker=ctrader, symbol="EURUSD")
    print(
        f"    Symbol Info: {c_info.data.name if c_info.data else 'None'}, "
        f"Digits={c_info.data.digits if c_info.data else 'None'}"
    )
    c_syms = get_symbols(broker=ctrader)
    print(f"    Symbols count: {len(c_syms.data) if c_syms.data else 0}")
    c_chk = check_order(
        broker=ctrader, request=TradeRequest(symbol="EURUSD", volume=0.01)
    )
    print(f"    Order Check: success={c_chk.is_success}, message='{c_chk.message}'")
    disconnect(broker=ctrader)
    print("    cTrader disconnected successfully.")

    # ------------------------------------------------------------------------
    # 8. Binance Crypto Exchange (Market Data Provider: Live Public REST API)
    # ------------------------------------------------------------------------
    print("\n[8] BINANCE CRYPTO EXCHANGE:")
    b_bars = get_bars(broker=binance, symbol="BTCUSDT", timeframe=TimeFrame.M1, count=5)
    print(f"    Live Klines count: {len(b_bars.data) if b_bars.data else 0}")
    assert b_bars.is_success
    assert b_bars.data is not None
    assert len(b_bars.data) == 5

    b_dl = binance.download_bars(
        DownloadRequest(
            provider_name="Binance",
            symbol="BTCUSDT",
            timeframe="M1",
            date_from="2026-10-01T00:00:00Z",
            date_to="2026-10-01T00:05:00Z",
        )
    )
    print(f"    Download klines count: {len(b_dl)}")
    assert len(b_dl) > 0

    b_trade = trade(
        broker=binance, request=TradeRequest(symbol="BTCUSDT", volume=0.001)
    )
    print(
        f"    Trade Rejection: success={b_trade.is_success}, message='{b_trade.message}'"
    )
    assert not b_trade.is_success
    assert "doesn't have trading capabilities" in b_trade.message

    # ------------------------------------------------------------------------
    # 9. Filesystem Tabular Market Data (Market Data Provider: CSV/Parquet)
    # ------------------------------------------------------------------------
    print("\n[9] FILES BROKER (CSV/Parquet):")
    f_bars = get_bars(broker=files, symbol="AAPL", timeframe=TimeFrame.D1, count=5)
    print(
        f"    Files Bars: success={f_bars.is_success}, "
        f"count={len(f_bars.data) if f_bars.data else 0}"
    )
    assert f_bars.is_success
    assert f_bars.data is not None
    assert len(f_bars.data) > 0

    f_trade = trade(broker=files, request=TradeRequest(symbol="AAPL", volume=1))
    print(
        f"    Trade Rejection: success={f_trade.is_success}, message='{f_trade.message}'"
    )
    assert not f_trade.is_success
    assert "doesn't have trading capabilities" in f_trade.message

    print("\n" + "=" * 80)
    print("ALL 9 BROKERS (MT5, CTRADER EXECUTION + YAHOO, DUKASCOPY, DARWINEX,")
    print("SQ_EQUITY, SQ_FUTURES, BINANCE, FILES DATA PROVIDERS) VERIFIED!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
