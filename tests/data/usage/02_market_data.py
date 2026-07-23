"""Demonstrate FEAT-DATA-02 market-data retrieval surface across all sources."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.contracts import DataError
from app.services.data.market_data import (
    AvailabilityRequest,
    MarketDataRequest,
    SymbolListRequest,
    SymbolMetadataRequest,
    get_data_availability,
    get_market_data,
    get_symbol_metadata,
    get_tick_data,
    list_symbols,
)
from app.services.data.transformation.tabular import (
    to_ohlcv_dataframe,
    to_tick_dataframe,
)
from app.utils import generate_id

_START = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_END = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_YAHOO_SESSION_START = datetime(2026, 6, 1, 13, 30, tzinfo=UTC)
_YAHOO_SESSION_END = datetime(2026, 6, 1, 20, 0, tzinfo=UTC)
_BINANCE_SOURCE = "binance_spot"


def _print_header(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 100)
    print(f"\t\t {title} ")
    print("=" * 100)


def example_01_mt5_bars() -> None:
    """Retrieve MT5 OHLCV bar dataset via public get_market_data."""
    _print_header("EXAMPLE 01: MT5 Bars")
    req_id = generate_id("req")
    req = MarketDataRequest(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=_START,
        end=_END,
        limit=100,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=req_id,
    )
    try:
        data = get_market_data(req)
        print(f"MT5 Data: {data.symbol} records={data.record_count}")
        print(to_ohlcv_dataframe(data))
    except DataError as exc:
        print(f"MT5 example handled: {exc.code}")


def example_02_mt5_ticks() -> None:
    """Retrieve MT5 tick dataset via public get_tick_data."""
    _print_header("EXAMPLE 02: MT5 Ticks")
    req_id = generate_id("req")
    req = MarketDataRequest(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="ticks",
        start=_START,
        end=_END,
        limit=100,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=req_id,
    )
    try:
        data = get_tick_data(req)
        print(f"MT5 Ticks Data: {data.symbol} records={data.record_count}")
        print(to_tick_dataframe(data))
    except DataError as exc:
        print(f"MT5 Ticks example handled: {exc.code}")


def example_03_dukascopy() -> None:
    """Retrieve Dukascopy OHLCV data via public get_market_data."""
    _print_header("EXAMPLE 03: Dukascopy")
    req_id = generate_id("req")
    req = MarketDataRequest(
        source_id="dukascopy",
        symbol="EURUSD",
        data_kind="bars",
        timeframe="H1",
        start=_START,
        end=_END,
        limit=100,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=req_id,
    )
    try:
        data = get_market_data(req)
        print(f"Dukascopy Data: {data.symbol} records={data.record_count}")
        print(to_ohlcv_dataframe(data))
    except DataError as exc:
        print(f"Dukascopy example handled: {exc.code}")


def example_04_yahoo() -> None:
    """Retrieve Yahoo Finance OHLCV data via public get_market_data."""
    _print_header("EXAMPLE 04: Yahoo Finance")
    req_id = generate_id("req")
    req = MarketDataRequest(
        source_id="yahoo",
        symbol="AAPL",
        data_kind="bars",
        timeframe="H1",
        start=_YAHOO_SESSION_START,
        end=_YAHOO_SESSION_END,
        limit=100,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=req_id,
    )
    try:
        data = get_market_data(req)
        print(f"Yahoo Data: {data.symbol} records={data.record_count}")
        print(to_ohlcv_dataframe(data))
    except DataError as exc:
        print(f"Yahoo example handled: {exc.code}")


def example_05_binance() -> None:
    """Retrieve Binance OHLCV data via public get_market_data."""
    _print_header("EXAMPLE 05: Binance")
    req_id = generate_id("req")
    req = MarketDataRequest(
        source_id=_BINANCE_SOURCE,
        symbol="BTCUSDT",
        data_kind="bars",
        timeframe="H1",
        start=_START,
        end=_END,
        limit=100,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=req_id,
    )
    try:
        data = get_market_data(req)
        print(f"Binance Data: {data.symbol} records={data.record_count}")
        print(to_ohlcv_dataframe(data))
    except DataError as exc:
        print(f"Binance example handled: {exc.code}")


def example_06_symbol_discovery() -> None:
    """Discover symbols per source using list_symbols."""
    _print_header("EXAMPLE 06: Symbol Discovery")
    req_id = generate_id("req")
    req = SymbolListRequest(
        source_id=_BINANCE_SOURCE,
        query="BTC",
        limit=100,
        request_id=req_id,
    )
    try:
        symbols = list_symbols(req)
        print(f"List symbols: count={len(symbols.items)}")
        print(symbols.items)
    except DataError as exc:
        print(f"Symbol discovery handled: {exc.code}")


def example_07_symbol_metadata() -> None:
    """Inspect symbol metadata via get_symbol_metadata."""
    _print_header("EXAMPLE 07: Symbol Metadata")
    req_id = generate_id("req")
    req = SymbolMetadataRequest(
        source_id=_BINANCE_SOURCE,
        symbol="BTCUSDT",
        request_id=req_id,
    )
    try:
        metadata = get_symbol_metadata(req)
        print(
            f"Symbol metadata: {metadata.canonical_symbol} "
            f"asset_class={metadata.asset_class}"
        )
    except DataError as exc:
        print(f"Symbol metadata handled: {exc.code}")


def example_08_data_availability() -> None:
    """Inspect source availability via get_data_availability."""
    _print_header("EXAMPLE 08: Data Availability")
    req_id = generate_id("req")
    req = AvailabilityRequest(
        source_id=_BINANCE_SOURCE,
        symbol="BTCUSDT",
        data_kind="ohlcv",
        timeframe="H1",
        start=_START,
        end=_END,
        max_probe_records=1000,
        request_id=req_id,
    )
    try:
        availability = get_data_availability(req)
        print(
            f"Data availability: {availability.symbol} "
            f"records={availability.record_count} "
            f"completeness={availability.completeness}"
        )
    except DataError as exc:
        print(f"Data availability handled: {exc.code}")


def main() -> None:
    """Run all market data retrieval examples across sources."""
    example_01_mt5_bars()
    example_02_mt5_ticks()
    example_03_dukascopy()
    example_04_yahoo()
    example_05_binance()
    example_06_symbol_discovery()
    example_07_symbol_metadata()
    example_08_data_availability()


if __name__ == "__main__":
    main()
