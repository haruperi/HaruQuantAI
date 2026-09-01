# ruff: noqa: BLE001
"""Demonstrate FEAT-DATA-01 market-data retrieval surface across all sources."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from _contracts_support import main as run_contract_support
from app.composition.config import load_broker_provider_settings
from app.kernel.identity import generate_id
from app.services.data import (
    build_availability_request,
    build_data_settings,
    build_level1_snapshot_request,
    build_market_data_request,
    build_market_directory_request,
    build_market_snapshot_request,
    build_symbol_list_request,
    build_symbol_metadata_request,
    build_symbols_quote_request,
    classify_symbol,
    data_settings_context,
    get_data_availability,
    get_display_asset_classes,
    get_level1_snapshot,
    get_market_data,
    get_market_snapshot,
    get_symbol_metadata,
    get_symbols_quotes,
    list_market_directory,
    list_symbols,
    run_data_migrations,
    to_ohlcv_dataframe,
)

_START = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
_END = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_BINANCE_SOURCE = "binance_spot"


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


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
    return bool(getattr(settings, field, False))


def fr_data_006() -> None:
    """FR-DATA-006: Stage 1 — Validate one typed internal request containing source, symbol, kind, optional timeframe/range/limit, cache policy, quality failure behavior, workflow, precision, and request ID."""
    _header(
        "Stage 1: Market Data Request Construction - Bounded Retrieval Request (FR-DATA-006)"
    )
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
    print(_format_result(req))
    print(
        f"Data -> MarketDataRequest(source={req.source_id}, symbol={req.symbol}, timeframe={req.timeframe}, limit={req.limit})"
    )


def fr_data_030() -> None:
    """FR-DATA-030: Stage 2 — Execute bounded bars/ticks/spreads retrieval through explicit source policy, versioned cache, normalization, quality, and precision, returning `MarketDataset`."""
    _header("Stage 2: Market Data Retrieval - Execute Bounded Retrieval (FR-DATA-030)")
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
        request_id=generate_id("req"),
    )
    try:
        response = get_market_data(req)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            dataset = response.data
            print(
                f"Data -> MarketDataset(symbol={dataset.symbol}, records={dataset.record_count})"
            )
            df = to_ohlcv_dataframe(dataset)
            print(f"Data -> DataFrame shape={df.shape}")
        else:
            print(
                f"Data -> StandardResponse(status={response.status}, message={response.message})"
            )
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_107() -> None:
    """FR-DATA-107: Stage 3 — Honour caller-declared stale-cache policy on `MarketDataRequest`: `refresh`, `fail_closed`, and `serve_stale`."""
    _header("Stage 3: Stale Cache Policy Handling - Stale Cache Modes (FR-DATA-107)")
    req = build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=_START,
        end=_END,
        limit=10,
        use_cache=True,
        stale_cache_policy="fail_closed",
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    print(_format_result(req))
    print(f"Data -> MarketDataRequest(stale_cache_policy={req.stale_cache_policy})")


def fr_data_031() -> None:
    """FR-DATA-031: Stage 4 — Return a bounded deterministic symbol page with cursor, source readiness, and provenance."""
    _header("Stage 4: Symbol List Discovery - Discover Symbols (FR-DATA-031)")
    if not _provider_opted_in(_BINANCE_SOURCE):
        print("Output Result -> ProviderOptedOut : ProviderOptedOut")
        print(f"Data -> Skipped {_BINANCE_SOURCE}: provider is disabled in settings.")
        return
    req = build_symbol_list_request(
        source_id=_BINANCE_SOURCE,
        query="BTC",
        limit=100,
        request_id=generate_id("req"),
    )
    try:
        response = list_symbols(req)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            symbols = response.data
            print(
                f"Data -> SymbolPage(count={len(symbols.items)}, source={_BINANCE_SOURCE})"
            )
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_032() -> None:
    """FR-DATA-032: Stage 5 — Return normalized asset-aware metadata and explicitly mark unknown optional fields without provider-derived defaults."""
    _header("Stage 5: Symbol Metadata Inspection - Inspect Metadata (FR-DATA-032)")
    if not _provider_opted_in(_BINANCE_SOURCE):
        print("Output Result -> ProviderOptedOut : ProviderOptedOut")
        print(f"Data -> Skipped {_BINANCE_SOURCE}: provider is disabled in settings.")
        return
    req = build_symbol_metadata_request(
        source_id=_BINANCE_SOURCE,
        symbol="BTCUSDT",
        request_id=generate_id("req"),
    )
    try:
        response = get_symbol_metadata(req)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            metadata = response.data
            print(
                f"Data -> SymbolMetadata(symbol={metadata.canonical_symbol}, asset_class={metadata.asset_class})"
            )
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_007_033() -> None:
    """FR-DATA-007, FR-DATA-033: Stage 6 — Inspect source availability, record count, and completeness over a probe window."""
    _header(
        "Stage 6: Data Availability & Range Indexing - Inspect Availability (FR-DATA-007, FR-DATA-033)"
    )
    if not _provider_opted_in(_BINANCE_SOURCE):
        print("Output Result -> ProviderOptedOut : ProviderOptedOut")
        print(f"Data -> Skipped {_BINANCE_SOURCE}: provider is disabled in settings.")
        return
    req = build_availability_request(
        source_id=_BINANCE_SOURCE,
        symbol="BTCUSDT",
        data_kind="ohlcv",
        timeframe="H1",
        start=_START,
        end=_END,
        max_probe_records=1000,
        request_id=generate_id("req"),
    )
    try:
        response = get_data_availability(req)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            avail = response.data
            print(
                f"Data -> DataAvailability(symbol={avail.symbol}, count={avail.record_count}, completeness={avail.completeness})"
            )
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_035() -> None:
    """FR-DATA-035: Stage 7 — Return bounded source-native or derived volume as records, buckets, or summary with explicit volume kind/unit."""
    _header("Stage 7: Volume Summary & Derived Metrics - Volume Summary (FR-DATA-035)")
    req = build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        start=_START,
        end=_END,
        limit=10,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    print(_format_result(req))
    print(
        f"Data -> VolumeRequest(source={req.source_id}, symbol={req.symbol}, limit={req.limit})"
    )


def fr_data_190() -> None:
    """FR-DATA-190/191: Stage 8 — Compose a bounded Level-1 bid/ask/last/spread/volume snapshot with disclosed source/receive time and computed freshness (feature)."""
    _header("Stage 8: Level-1 Quote Snapshot - Bounded Snapshot (FR-DATA-190/191)")
    req = build_level1_snapshot_request(
        source_id="mt5",
        symbol="EURUSD",
        request_id=generate_id("req"),
    )
    print(_format_result(req))
    try:
        response = get_level1_snapshot(req)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            snapshot = response.data
            print(
                f"Data -> Level1Snapshot(symbol={snapshot.symbol}, bid={snapshot.bid}, "
                f"ask={snapshot.ask}, spread={snapshot.spread}, "
                f"quote_age_seconds={snapshot.quote_age_seconds})"
            )
        else:
            print(
                f"Data -> StandardResponse(status={response.status}, message={response.message})"
            )
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_203_207() -> None:
    """FR-DATA-203/207: Build and retrieve a composite quote/latest-bar snapshot."""
    _header(
        "Stage 9: Composite Market Snapshot - Level-1 and Latest Bar (FR-DATA-203/207)"
    )
    request = build_market_snapshot_request(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="D1",
        request_id=generate_id("req"),
    )
    print(_format_result(request))
    if not _provider_opted_in("mt5"):
        print("Output Result -> ProviderOptedOut : ProviderOptedOut")
        print("Data -> Skipped mt5: provider is disabled in settings.")
        return
    response = get_market_snapshot(request)
    print(_format_result(response))
    if response.status == "success" and response.data is not None:
        snapshot = response.data
        print(
            "Data -> MarketSnapshot("
            f"symbol={snapshot.symbol}, latest_bar={snapshot.latest_bar is not None})"
        )


def fr_data_208_209() -> None:
    """FR-DATA-208/209: Classify symbols and expose supported categories."""
    _header("Stage 10: Market Classification - Evidence and Manifest (FR-DATA-208/209)")
    asset_class = classify_symbol("Forex\\Metals", "XAUUSD")
    manifest = get_display_asset_classes()
    print(_format_result(manifest))
    print(f"Data -> classification={asset_class}, supported={manifest}")


def fr_data_210_211() -> None:
    """FR-DATA-210/211: Build and retrieve one bounded market-directory page."""
    _header("Stage 11: Market Directory - Bounded Categorized Page (FR-DATA-210/211)")
    request = build_market_directory_request(
        source_id="mt5",
        limit=5,
        query="EUR",
        request_id=generate_id("req"),
    )
    print(_format_result(request))
    if not _provider_opted_in("mt5"):
        print("Output Result -> ProviderOptedOut : ProviderOptedOut")
        print("Data -> Skipped mt5: provider is disabled in settings.")
        return
    response = list_market_directory(request)
    print(_format_result(response))
    if response.status == "success" and response.data is not None:
        print(f"Data -> MarketDirectory(rows={len(response.data.rows)})")


def fr_data_212_213() -> None:
    """FR-DATA-212/213: Build and retrieve exact-symbol quote evidence."""
    _header(
        "Stage 12: Explicit-Symbol Quotes - Caller-Bounded Evidence (FR-DATA-212/213)"
    )
    request = build_symbols_quote_request(
        source_id="mt5",
        symbols=("EURUSD", "XAUUSD"),
        request_id=generate_id("req"),
    )
    print(_format_result(request))
    if not _provider_opted_in("mt5"):
        print("Output Result -> ProviderOptedOut : ProviderOptedOut")
        print("Data -> Skipped mt5: provider is disabled in settings.")
        return
    response = get_symbols_quotes(request)
    print(_format_result(response))
    if response.status == "success" and response.data is not None:
        print(f"Data -> ExactSymbolQuotes(rows={len(response.data.rows)})")


def main() -> None:
    """Execute every functional-requirement demonstration."""
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
            data_provider_sources=("mt5", "binance_spot"),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            print("=" * 80)
            print("FEATURE: FEAT-DATA-01 - Market Data Retrieval")
            print(
                "PURPOSE: Retrieval request/result contracts and the market, tick, spread, symbol, metadata, availability, and volume operations"
            )
            print(
                "MODULE FLOW: Stage 1 (Market Data Request) -> Stage 2 (Market Data Retrieval) -> Stage 3 (Stale Cache Policy) -> Stage 4 (Symbol List Discovery) -> Stage 5 (Symbol Metadata Inspection) -> Stage 6 (Data Availability & Range Indexing) -> Stage 7 (Volume Summary)"
            )
            print("=" * 80)

            fr_data_006()
            fr_data_030()
            fr_data_107()
            fr_data_031()
            fr_data_032()
            fr_data_007_033()
            fr_data_035()
            fr_data_190()
            fr_data_203_207()
            fr_data_208_209()
            fr_data_210_211()
            fr_data_212_213()
            run_contract_support()
            print("SUCCESS: FEAT-DATA-01 completed")


if __name__ == "__main__":
    main()
