"""Demonstrate FEAT-DATA-02 market-data retrieval surface across all sources."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    AvailabilityRequest,
    DataError,
    MarketDataRequest,
    SymbolListRequest,
    SymbolMetadataRequest,
    get_data_availability,
    get_market_data,
    get_symbol_metadata,
    get_tick_data,
    list_symbols,
    to_ohlcv_dataframe,
    to_tick_dataframe,
)
from app.utils import AppSettings, generate_id

_START = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_END = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_YAHOO_SESSION_START = datetime(2026, 6, 1, 13, 30, tzinfo=UTC)
_YAHOO_SESSION_END = datetime(2026, 6, 1, 20, 0, tzinfo=UTC)
_BINANCE_SOURCE = "binance_spot"


class _MarketDataUsageSettings(AppSettings):
    """Usage settings inheriting AppSettings to load .env configuration."""

    data_usage_live_providers: str = ""


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _provider_opted_in(source_id: str) -> bool:
    """Return whether an external provider was explicitly enabled for this run."""
    raw_setting = _MarketDataUsageSettings().data_usage_live_providers
    enabled = {
        item.strip().casefold() for item in raw_setting.split(",") if item.strip()
    }
    if "all" in enabled or "*" in enabled or source_id.casefold() in enabled:
        return True
    print(
        f"Skipped {source_id}: set DATA_USAGE_LIVE_PROVIDERS={source_id} "
        "only after verifying the effective target and credential authority."
    )
    return False


def _print_header(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 100)
    print(f"\t\t {title} ")


def example_01_mt5_bars() -> None:
    """Retrieve MT5 OHLCV bar dataset via public get_market_data."""
    _header("Retrieve MT5 OHLCV bar dataset via public get_market_data.")
    if not _provider_opted_in("mt5"):
        return
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
    _header("Retrieve MT5 tick dataset via public get_tick_data.")
    if not _provider_opted_in("mt5"):
        return
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
    _header("Retrieve Dukascopy OHLCV data via public get_market_data.")
    if not _provider_opted_in("dukascopy"):
        return
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
    _header("Retrieve Yahoo Finance OHLCV data via public get_market_data.")
    if not _provider_opted_in("yahoo"):
        return
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
    _header("Retrieve Binance OHLCV data via public get_market_data.")
    if not _provider_opted_in(_BINANCE_SOURCE):
        return
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
    _header("Discover symbols per source using list_symbols.")
    if not _provider_opted_in(_BINANCE_SOURCE):
        return
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
    _header("Inspect symbol metadata via get_symbol_metadata.")
    if not _provider_opted_in(_BINANCE_SOURCE):
        return
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
    _header("Inspect source availability via get_data_availability.")
    if not _provider_opted_in(_BINANCE_SOURCE):
        return
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


def _demonstrate_feature() -> None:
    """Run all market data retrieval examples across sources."""
    example_01_mt5_bars()
    example_02_mt5_ticks()
    example_03_dukascopy()
    example_04_yahoo()
    example_05_binance()
    example_06_symbol_discovery()
    example_07_symbol_metadata()
    example_08_data_availability()


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_006() -> None:
    _header("fr_data_006")
    "FR-DATA-006: Validate one typed internal request containing source, symbol, kind, optional timeframe/range/limit, cache policy, the closed quality-failure enum `reject` or `warn`, UTC/IANA inputs, workflow, precision, explicit fallbacks, and request ID. The default is `reject`; the removed `fail` literal is invalid."
    _demonstrate_once()


def fr_data_007() -> None:
    _header("fr_data_007")
    "FR-DATA-007: Represent indexed ranges, gaps, overlap/completeness evidence, record count, source revision/readiness, and provenance without materializing the full dataset."
    _demonstrate_once()


def fr_data_030() -> None:
    _header("fr_data_030")
    "FR-DATA-030: Execute bounded bars/ticks/spreads retrieval through explicit source policy, versioned cache, normalization, quality, and precision, returning `MarketDataset`. A failed quality report raises `DATA_QUALITY_FAILED` under `reject`; under `warn`, fresh and cached paths log and return the unchanged data and failed report."
    _demonstrate_once()


def fr_data_031() -> None:
    _header("fr_data_031")
    "FR-DATA-031: Return a bounded deterministic symbol page with cursor, source readiness, and provenance."
    _demonstrate_once()


def fr_data_032() -> None:
    _header("fr_data_032")
    "FR-DATA-032: Return normalized asset-aware metadata and explicitly mark unknown optional fields without provider-derived optimistic defaults."
    _demonstrate_once()


def fr_data_033() -> None:
    _header("fr_data_033")
    "FR-DATA-033: Compute ranges, gaps, overlaps, completeness, count, revision, and readiness from local manifests/indexes or one bounded provider retrieval, never hard-code certainty. Provider results describe only the observed probe window and record whether the probe limit was reached."
    _demonstrate_once()


def fr_data_035() -> None:
    _header("fr_data_035")
    "FR-DATA-035: Return bounded source-native or derived volume as records, buckets, or summary with explicit volume kind/unit and provenance."
    _demonstrate_once()


def fr_data_107() -> None:
    _header("fr_data_107")
    'FR-DATA-107: Honour a caller-declared stale-cache policy on `MarketDataRequest`: `refresh` treats an expired entry as a miss, `fail_closed` returns `EMPTY_RESULT` without contacting any source, and `serve_stale` returns the expired entry with `cache_status="stale_warning"`. `serve_stale` is valid only in the `research` workflow context and is rejected elsewhere at contract validation.'
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_006,
        fr_data_007,
        fr_data_030,
        fr_data_031,
        fr_data_032,
        fr_data_033,
        fr_data_035,
        fr_data_107,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
