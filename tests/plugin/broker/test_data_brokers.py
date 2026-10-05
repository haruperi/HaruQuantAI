"""Unit tests for market data broker plugins (SQ Equity, SQ Futures, Darwinex, Yahoo, Dukascopy)."""

from __future__ import annotations

from app.plugin.broker import (
    TimeFrame,
    darwinex,
    dukascopy,
    get_bars,
    get_symbol_info,
    get_symbols,
    sq_equity,
    sq_futures,
    yahoo,
)


def test_sq_equity_catalog_and_parquet() -> None:
    """Verify SQ Equity metadata and local Parquet reading."""
    sym_res = get_symbol_info(broker=sq_equity, symbol="AAPL")
    assert sym_res.is_success is True
    assert sym_res.data is not None
    assert sym_res.data.name == "AAPL"
    assert sym_res.data.digits == 2
    assert sym_res.data.currency_base == "USD"

    syms_list = get_symbols(broker=sq_equity)
    assert syms_list.is_success is True
    assert len(syms_list.data) >= 10

    # Read bars from data/market/sq_equity
    bars_res = get_bars(
        broker=sq_equity, symbol="AAPL", timeframe=TimeFrame.D1, count=5
    )
    assert bars_res.is_success is True
    assert len(bars_res.data) == 5
    bar = bars_res.data[-1]
    assert bar.high >= bar.low
    assert bar.open > 0
    assert bar.close > 0


def test_sq_futures_catalog_and_parquet() -> None:
    """Verify SQ Futures contract specs and local Parquet reading."""
    sym_res = get_symbol_info(broker=sq_futures, symbol="@ES")
    assert sym_res.is_success is True
    assert sym_res.data is not None
    assert sym_res.data.name == "@ES"
    assert sym_res.data.trade_contract_size == 50.0
    assert sym_res.data.point == 0.25
    assert sym_res.metadata.extensions.get("source") == "database"

    # Verify query for @CL (Crude Oil)
    cl_res = get_symbol_info(broker=sq_futures, symbol="@CL")
    assert cl_res.is_success is True
    assert cl_res.data is not None
    assert cl_res.data.trade_contract_size == 1000.0
    assert cl_res.data.point == 0.01

    # Verify error failure response for unknown commodity (no fallback)
    unk_res = get_symbol_info(broker=sq_futures, symbol="UNKNOWN_FUT")
    assert unk_res.is_success is False
    assert unk_res.data is None
    assert unk_res.error is not None
    assert unk_res.error.code == "SYMBOL_NOT_FOUND"

    syms_list = get_symbols(broker=sq_futures)
    assert syms_list.is_success is True
    assert len(syms_list.data) >= 10

    # Read bars from data/market/sq_futures
    bars_res = get_bars(
        broker=sq_futures, symbol="@ES", timeframe=TimeFrame.D1, count=5
    )
    assert bars_res.is_success is True
    assert len(bars_res.data) == 5
    bar = bars_res.data[-1]
    assert bar.high >= bar.low
    assert bar.close > 0


def test_darwinex_catalog() -> None:
    """Verify Darwinex embedded instrument catalog."""
    sym_res = get_symbol_info(broker=darwinex, symbol="EURUSD")
    assert sym_res.is_success is True
    assert sym_res.data is not None
    assert sym_res.data.name == "EURUSD"
    assert sym_res.data.digits == 5
    assert sym_res.data.point == 0.00001
    assert sym_res.data.trade_contract_size == 100000.0

    syms = get_symbols(broker=darwinex)
    assert syms.is_success is True
    assert len(syms.data) >= 10


def test_dukascopy_catalog() -> None:
    """Verify Dukascopy embedded catalog and specs."""
    sym_res = get_symbol_info(broker=dukascopy, symbol="EURUSD")
    assert sym_res.is_success is True
    assert sym_res.data is not None
    assert sym_res.data.name == "EURUSD"
    assert sym_res.data.digits == 5
    assert sym_res.data.point == 0.00001
    assert sym_res.data.trade_contract_size == 100000.0

    syms = get_symbols(broker=dukascopy)
    assert syms.is_success is True
    assert len(syms.data) >= 10


def test_yahoo_interval_mapping() -> None:
    """Verify Yahoo timeframe to query interval mapping."""
    assert yahoo._map_interval(TimeFrame.M1) == "1m"
    assert yahoo._map_interval(TimeFrame.M5) == "5m"
    assert yahoo._map_interval(TimeFrame.H1) == "60m"
    assert yahoo._map_interval(TimeFrame.D1) == "1d"
    assert yahoo._map_interval(TimeFrame.W1) == "1wk"
    assert yahoo._map_interval("15M") == "15m"
