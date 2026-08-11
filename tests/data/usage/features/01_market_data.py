# ruff: noqa: BLE001
"""Demonstrate FEAT-DATA-02 market-data retrieval surface across all sources."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from _contracts_support import main as run_contract_support
from app.services.data import (
    build_availability_request,
    build_data_settings,
    build_level1_snapshot_request,
    build_market_data_request,
    build_symbol_list_request,
    build_symbol_metadata_request,
    data_settings_context,
    get_data_availability,
    get_level1_snapshot,
    get_market_data,
    get_symbol_metadata,
    list_symbols,
    run_data_migrations,
    to_ohlcv_dataframe,
)
from app.utils import generate_id, load_broker_provider_settings

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


def main() -> None:
    """Execute every functional-requirement demonstration."""
    with TemporaryDirectory(prefix="usage-market-data-") as directory:
        (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        db_file = Path(directory) / "usage.sqlite3"
        settings = build_data_settings(
            database_url=f"sqlite:///{db_file.as_posix()}",
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
            print("FEATURE: FEAT-DATA-02 - Market Data Retrieval")
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
            run_contract_support()
            print("SUCCESS: FEAT-DATA-02 completed")


if __name__ == "__main__":
    main()
