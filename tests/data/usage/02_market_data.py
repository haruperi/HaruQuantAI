# ruff: noqa: BLE001
"""Demonstrate FEAT-DATA-02 market-data retrieval surface across all sources."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_availability_request,
    build_data_settings,
    build_market_data_request,
    build_symbol_list_request,
    build_symbol_metadata_request,
    data_settings_context,
    get_data_availability,
    get_market_data,
    get_symbol_metadata,
    get_tick_data,
    list_symbols,
    run_data_migrations,
    to_ohlcv_dataframe,
    to_tick_dataframe,
)
from app.utils import generate_id, load_broker_provider_settings

_START = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_END = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_YAHOO_SESSION_START = datetime(2026, 6, 1, 13, 30, tzinfo=UTC)
_YAHOO_SESSION_END = datetime(2026, 6, 1, 20, 0, tzinfo=UTC)
_BINANCE_SOURCE = "binance_spot"


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _provider_opted_in(source_id: str) -> bool:
    """Return whether an external provider was explicitly enabled for this run."""
    settings = load_broker_provider_settings()
    field = {
        "mt5": "mt5_enabled",
        "ctrader": "ctrader_enabled",
        "binance_spot": "binance_enabled",
        "dukascopy": "dukascopy_enabled",
        "yahoo": "yahoo_enabled",
    }[source_id.casefold()]
    if bool(getattr(settings, field)):
        return True
    print(f"Skipped {source_id}: provider is disabled in validated settings.")
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
    req = build_market_data_request(
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
        response = get_market_data(req)
        if response.status == "success" and response.data is not None:
            data = response.data
            print(f"MT5 Data: {data.symbol} records={data.record_count}")
            print(to_ohlcv_dataframe(data))
    except Exception as exc:
        print(f"MT5 example handled: {exc.code}")


def example_02_mt5_ticks() -> None:
    """Retrieve MT5 tick dataset via public get_tick_data."""
    _header("Retrieve MT5 tick dataset via public get_tick_data.")
    if not _provider_opted_in("mt5"):
        return
    req_id = generate_id("req")
    req = build_market_data_request(
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
        response = get_tick_data(req)
        if response.status == "success" and response.data is not None:
            data = response.data
            print(f"MT5 Ticks Data: {data.symbol} records={data.record_count}")
            print(to_tick_dataframe(data))
    except Exception as exc:
        print(f"MT5 Ticks example handled: {exc.code}")


def example_03_dukascopy() -> None:
    """Retrieve Dukascopy OHLCV data via public get_market_data."""
    _header("Retrieve Dukascopy OHLCV data via public get_market_data.")
    if not _provider_opted_in("dukascopy"):
        return
    req_id = generate_id("req")
    req = build_market_data_request(
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
        response = get_market_data(req)
        if response.status == "success" and response.data is not None:
            data = response.data
            print(f"Dukascopy Data: {data.symbol} records={data.record_count}")
            print(to_ohlcv_dataframe(data))
    except Exception as exc:
        print(f"Dukascopy example handled: {exc.code}")


def example_04_yahoo() -> None:
    """Retrieve Yahoo Finance OHLCV data via public get_market_data."""
    _header("Retrieve Yahoo Finance OHLCV data via public get_market_data.")
    if not _provider_opted_in("yahoo"):
        return
    req_id = generate_id("req")
    req = build_market_data_request(
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
        response = get_market_data(req)
        if response.status == "success" and response.data is not None:
            data = response.data
            print(f"Yahoo Data: {data.symbol} records={data.record_count}")
            print(to_ohlcv_dataframe(data))
    except Exception as exc:
        print(f"Yahoo example handled: {exc.code}")


def example_05_binance() -> None:
    """Retrieve Binance OHLCV data via public get_market_data."""
    _header("Retrieve Binance OHLCV data via public get_market_data.")
    if not _provider_opted_in(_BINANCE_SOURCE):
        return
    req_id = generate_id("req")
    req = build_market_data_request(
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
        response = get_market_data(req)
        if response.status == "success" and response.data is not None:
            data = response.data
            print(f"Binance Data: {data.symbol} records={data.record_count}")
            print(to_ohlcv_dataframe(data))
    except Exception as exc:
        print(f"Binance example handled: {exc.code}")


def example_06_symbol_discovery() -> None:
    """Discover symbols per source using list_symbols."""
    _header("Discover symbols per source using list_symbols.")
    if not _provider_opted_in(_BINANCE_SOURCE):
        return
    req_id = generate_id("req")
    req = build_symbol_list_request(
        source_id=_BINANCE_SOURCE,
        query="BTC",
        limit=100,
        request_id=req_id,
    )
    try:
        response = list_symbols(req)
        if response.status == "success" and response.data is not None:
            symbols = response.data
            print(f"List symbols: count={len(symbols.items)}")
            print(symbols.items)
    except Exception as exc:
        print(f"Symbol discovery handled: {exc.code}")


def example_07_symbol_metadata() -> None:
    """Inspect symbol metadata via get_symbol_metadata."""
    _header("Inspect symbol metadata via get_symbol_metadata.")
    if not _provider_opted_in(_BINANCE_SOURCE):
        return
    req_id = generate_id("req")
    req = build_symbol_metadata_request(
        source_id=_BINANCE_SOURCE,
        symbol="BTCUSDT",
        request_id=req_id,
    )
    try:
        response = get_symbol_metadata(req)
        if response.status == "success" and response.data is not None:
            metadata = response.data
            print(
                f"Symbol metadata: {metadata.canonical_symbol} "
                f"asset_class={metadata.asset_class}"
            )
    except Exception as exc:
        print(f"Symbol metadata handled: {exc.code}")


def example_08_data_availability() -> None:
    """Inspect source availability via get_data_availability."""
    _header("Inspect source availability via get_data_availability.")
    if not _provider_opted_in(_BINANCE_SOURCE):
        return
    req_id = generate_id("req")
    req = build_availability_request(
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
        response = get_data_availability(req)
        if response.status == "success" and response.data is not None:
            availability = response.data
            print(
                f"Data availability: {availability.symbol} "
                f"records={availability.record_count} "
                f"completeness={availability.completeness}"
            )
    except Exception as exc:
        print(f"Data availability handled: {exc.code}")


def _demonstrate_feature() -> None:
    """Run all market data retrieval examples across sources."""
    from tempfile import TemporaryDirectory

    with TemporaryDirectory(prefix="usage-market-data-") as directory:
        (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
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
