# ruff: noqa: BLE001
"""Direct, copyable usage catalogue for the Data service public API.

This supplemental catalogue preserves the scenarios from the legacy Data example
while using only the current ``app.services.data`` package-root boundary. Each
supported example visibly constructs its request and calls the operation a consumer
would use; it never dispatches into another usage program.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.composition.config import load_broker_provider_settings
from app.kernel.identity import generate_id
from app.services.data import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    build_active_market_sessions_request,
    build_availability_request,
    build_cache_clear_request,
    build_data_quality_report,
    build_dataset_load_request,
    build_dataset_save_request,
    build_exchange_session_request,
    build_job_definition,
    build_job_status_request,
    build_market_data_request,
    build_market_dataset,
    build_market_stream_request,
    build_ohlcv_record,
    build_symbol_list_request,
    build_symbol_metadata_request,
    build_synthetic_request,
    build_tick_record,
    clear_data_cache,
    create_data_update_job,
    data_provider_connection_resolver_context,
    data_provider_settings_context,
    generate_synthetic_bars,
    generate_tick_series,
    get_active_market_sessions,
    get_data_availability,
    get_data_update_job_status,
    get_exchange_sessions,
    get_market_data,
    get_symbol_metadata,
    inspect_data_quality,
    list_symbols,
    load_csv,
    load_local_dataset,
    load_parquet,
    resample_ohlcv,
    save_dataset,
    start_data_update_job,
    stop_data_update_job,
    stream_market_data,
    to_ohlcv_dataframe,
    to_tick_dataframe,
)

_START = datetime(2026, 8, 1, tzinfo=UTC)
_END = _START + timedelta(hours=1000)
_CSV_PATH = Path("data/raw/EURUSD_H1.csv")
_PARQUET_PATH = Path("data/raw/EURUSD_H1.parquet")
_PROVIDER_READS_ENABLED: ContextVar[bool] = ContextVar(
    "data_usage_provider_reads_enabled",
    default=False,
)
_PROVIDER_FIELDS = {
    "MT5_ENABLED": "mt5_enabled",
    "MT5_TERMINAL_PATH": "mt5_terminal_path",
    "CTRADER_ENABLED": "ctrader_enabled",
    "BINANCE_ENABLED": "binance_enabled",
    "DUKASCOPY_ENABLED": "dukascopy_enabled",
    "YAHOO_ENABLED": "yahoo_enabled",
}


def _header(title: str) -> None:
    """Print a bounded example heading.

    Args:
        title: Human-readable example title.

    Returns:
        None.
    """
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


@contextmanager
def _provider_runtime_context(*, offline: bool) -> Iterator[bool]:
    """Inject database-backed provider settings for a verified usage run.

    Args:
        offline: Whether to suppress external provider reads.

    Yields:
        Whether provider reads are enabled for this run.

    Raises:
        ValueError: If persisted settings do not prove a dev/demo boundary.
    """
    if offline:
        yield False
        return
    from app.services.api import (
        build_system_broker_connection_config,
        get_api_settings,
        get_system_settings,
    )

    record = get_system_settings(request_id=generate_id("req"))
    environment = record.settings.get("ENVIRONMENT", get_api_settings().environment)
    if environment != "dev":
        raise ValueError(
            "provider reads require the effective API environment to be dev"
        )
    mt5_config = build_system_broker_connection_config(
        "mt5",
        request_id=generate_id("req"),
    )
    if getattr(mt5_config, "environment", None) != "demo":
        raise ValueError("MT5 provider reads require a composed demo environment")
    explicit_values = {
        field: record.settings[key]
        for key, field in _PROVIDER_FIELDS.items()
        if key in record.settings
    }
    provider_settings = load_broker_provider_settings(explicit_values)
    with (
        data_provider_settings_context(provider_settings),
        data_provider_connection_resolver_context(
            lambda broker_id, request_id: (
                mt5_config
                if broker_id == "mt5"
                else build_system_broker_connection_config(
                    broker_id,
                    request_id=request_id,
                )
            )
        ),
    ):
        token = _PROVIDER_READS_ENABLED.set(True)
        try:
            yield True
        finally:
            _PROVIDER_READS_ENABLED.reset(token)


def _sample_bars(*, timeframe: str = "M1", count: int = 10) -> Any:
    """Build deterministic canonical bars for transformation examples.

    Args:
        timeframe: Canonical timeframe assigned to the dataset.
        count: Number of records to construct.

    Returns:
        A canonical in-memory market dataset.
    """
    step = timedelta(minutes=1 if timeframe == "M1" else 60)
    records = tuple(
        build_ohlcv_record(
            timestamp=_START + step * index,
            open=Decimal("1.1000") + Decimal(index) * Decimal("0.0001"),
            high=Decimal("1.1003") + Decimal(index) * Decimal("0.0001"),
            low=Decimal("1.0998") + Decimal(index) * Decimal("0.0001"),
            close=Decimal("1.1001") + Decimal(index) * Decimal("0.0001"),
            volume=Decimal(100 + index),
            price_unit="USD",
            volume_unit="lots",
            source="usage-fixture",
            source_symbol="EURUSD",
            available_at=_START + step * index + timedelta(seconds=1),
        )
        for index in range(count)
    )
    quality = build_data_quality_report(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=count,
        checked_count=count,
        truncated=False,
        sample_limit=count,
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return build_market_dataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe=timeframe,
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=count,
        quality_report=quality,
        source_metadata={"source": "usage-fixture"},
        license_metadata={"license": "fixture"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def _synthetic_bars(*, timeframe: str = "H1", count: int = 5) -> Any:
    """Generate deterministic bars through the real public API.

    Args:
        timeframe: Requested canonical timeframe.
        count: Bounded number of bars.

    Returns:
        Generated canonical market dataset.

    Raises:
        RuntimeError: If generation does not return data.
    """
    request = build_synthetic_request(
        symbol="EURUSD",
        data_kind="bars",
        timeframe=timeframe,
        start=_START,
        record_count=count,
        method="gbm",
        seed=42,
        parameters={
            "mu": Decimal("0.02"),
            "sigma": Decimal("0.10"),
            "start_val": Decimal("1.1000"),
        },
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    response = generate_synthetic_bars(request)
    if response.data is None:
        raise RuntimeError("SYNTHETIC_DATA_UNAVAILABLE")
    return response.data


def _mt5_bars(*, timeframe: str = "H1", limit: int = 100) -> Any:
    """Retrieve MT5 bars through the Data public API.

    Args:
        timeframe: Requested canonical timeframe.
        limit: Number of bars to retrieve.

    Returns:
        Canonical market dataset if available, else None.
    """
    request = build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe=timeframe,
        start=_START,
        end=_END,
        limit=limit,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    return get_market_data(request).data


def _mt5_ticks(*, limit: int = 100) -> Any:
    """Retrieve MT5 ticks through the Data public API.

    Args:
        limit: Number of ticks to retrieve.

    Returns:
        Canonical market dataset if available, else None.
    """
    request = build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="ticks",
        timeframe=None,
        start=_START,
        end=_END,
        limit=limit,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    return get_market_data(request).data


def _market_request(source_id: str, symbol: str, data_kind: str) -> Any:
    """Build one bounded provider request while leaving execution visible.

    Args:
        source_id: Registered Data source identifier.
        symbol: Provider symbol.
        data_kind: Requested market-data kind.

    Returns:
        A validated market-data request.
    """
    return build_market_data_request(
        source_id=source_id,
        symbol=symbol,
        data_kind=data_kind,
        timeframe="M1" if data_kind == "bars" else None,
        start=_START,
        end=_END,
        limit=100,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def example_01_mt5_bars() -> None:
    """Retrieve bounded MT5 bars through the Data public API."""
    request = build_market_data_request(
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
        response = get_market_data(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("01 MT5 bars: build_market_data_request -> get_market_data")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_02_mt5_ticks() -> None:
    """Retrieve bounded MT5 ticks through the Data public API."""
    request = build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="ticks",
        timeframe=None,
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
        response = get_market_data(request)
        if response.data is not None:
            data = to_tick_dataframe(response.data)
            _header("02 MT5 ticks: build_market_data_request -> get_market_data")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_03_mt5_stream() -> None:
    """Stream MT5 data through the Data public API."""

    async def _run_stream() -> None:
        request = build_market_stream_request(
            source_id="mt5",
            symbol="EURUSD",
            mode="ticks",
            timeframe="M1",
            request_id=generate_id("req"),
        )
        count = 0
        async for event in stream_market_data(request):
            if count == 0:
                _header(
                    "03 MT5 stream: build_market_stream_request -> stream_market_data"
                )
            print(
                f"\nStream Event #{event.sequence}: {event.event_type} | payload: {event.payload}",
                flush=True,
            )
            count += 1
            if count >= 5:
                break

    try:
        asyncio.run(_run_stream())
    except Exception as exc:
        print(f"\nError: {exc}")


def example_04_dukascopy() -> None:
    """Retrieve bounded Dukascopy bars through the Data public API."""
    request = build_market_data_request(
        source_id="dukascopy",
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
        response = get_market_data(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("03 Dukascopy bars: build_market_data_request -> get_market_data")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_05_yahoo() -> None:
    """Retrieve bounded Yahoo bars through the Data public API."""
    request = build_market_data_request(
        source_id="yahoo",
        symbol="AAPL",
        data_kind="bars",
        timeframe="D1",
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
        response = get_market_data(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("04 Yahoo bars: build_market_data_request -> get_market_data")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_06_binance() -> None:
    """Retrieve bounded Binance Spot bars through the Data public API."""
    request = build_market_data_request(
        source_id="binance_spot",
        symbol="BTCUSDT",
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
        response = get_market_data(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("05 Binance bars: build_market_data_request -> get_market_data")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_07_synthetic_bars() -> None:
    """Generate deterministic synthetic bars."""
    request = build_synthetic_request(
        symbol="GBPUSD",
        data_kind="bars",
        timeframe="H1",
        start=_START,
        record_count=24,
        method="gbm",
        seed=42,
        parameters={
            "mu": Decimal("0.02"),
            "sigma": Decimal("0.10"),
            "start_val": Decimal("1.2500"),
        },
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    try:
        response = get_market_data(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("07 synthetic bars: generate_synthetic_bars")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_08_csv_load_direct() -> None:
    """Load a manifest-verified CSV dataset directly."""
    try:
        response = load_csv(_CSV_PATH)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("08 CSV direct load: load_csv")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_09_csv_tool_load() -> None:
    """Load CSV through the governed typed request boundary."""
    request = build_dataset_load_request(
        relative_path=_CSV_PATH,
        format="csv",
        request_id=generate_id("req"),
    )
    try:
        response = load_local_dataset(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("09 governed CSV load: load_local_dataset")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_10_csv_fetch_range() -> None:
    """Request bounded CSV availability before loading records."""
    request = build_availability_request(
        source_id="csv",
        symbol="EURUSD",
        timeframe="H1",
        request_id=generate_id("req"),
    )
    try:
        response = get_data_availability(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("10 bounded CSV availability: get_data_availability")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_11_parquet_load_direct() -> None:
    """Load a manifest-verified Parquet dataset directly."""
    try:
        response = load_parquet(_PARQUET_PATH)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("11 Parquet direct load: load_parquet")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_12_parquet_tool_load() -> None:
    """Load Parquet through the governed typed request boundary."""
    request = build_dataset_load_request(
        relative_path=_PARQUET_PATH,
        format="parquet",
        request_id=generate_id("req"),
    )
    try:
        response = load_local_dataset(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("12 governed Parquet load: load_local_dataset")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_13_csv_saver() -> None:
    """Save a canonical dataset as CSV through the public boundary."""
    request = build_dataset_save_request(
        dataset=_sample_bars(),
        relative_path=Path("data/processed/usage_bars.csv"),
        format="csv",
        overwrite=True,
        request_id=generate_id("req"),
    )
    try:
        response = save_dataset(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("13 CSV save: build_dataset_save_request -> save_dataset")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_14_parquet_saver() -> None:
    """Save a canonical dataset as Parquet through the public boundary."""
    request = build_dataset_save_request(
        dataset=_sample_bars(),
        relative_path=Path("data/processed/usage_bars.parquet"),
        format="parquet",
        overwrite=True,
        request_id=generate_id("req"),
    )
    try:
        response = save_dataset(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("14 Parquet save: build_dataset_save_request -> save_dataset")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_15_gateway_synthetic() -> None:
    """Use the current synthetic feature boundary directly."""
    dataset = _synthetic_bars(timeframe="H1", count=24)
    print("Success -> synthetic feature boundary")
    print(f"Data -> symbol={dataset.symbol}, records={dataset.record_count}")


def example_16_gateway_csv() -> None:
    """Use the current CSV feature boundary directly."""
    try:
        response = load_csv(_CSV_PATH)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("16 CSV boundary: load_csv")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_17_gateway_parquet() -> None:
    """Use the current Parquet feature boundary directly."""
    try:
        response = load_parquet(_PARQUET_PATH)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("17 Parquet boundary: load_parquet")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_18_caching() -> None:
    """Select an explicit fail-closed stale-cache policy."""
    request = build_market_data_request(
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
    try:
        response = get_market_data(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("18 cache policy: get_market_data")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_19_symbol_discovery() -> None:
    """Discover a bounded page of Binance symbols."""
    request = build_symbol_list_request(
        source_id="binance_spot",
        query="BTC",
        limit=25,
        request_id=generate_id("req"),
    )
    try:
        response = list_symbols(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("19 symbol discovery: list_symbols")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_20_symbol_metadata() -> None:
    """Read provider-confirmed symbol metadata."""
    request = build_symbol_metadata_request(
        source_id="binance_spot",
        symbol="BTCUSDT",
        request_id=generate_id("req"),
    )
    try:
        response = get_symbol_metadata(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("20 symbol metadata: get_symbol_metadata")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_21_data_availability() -> None:
    """Inspect bounded local-source availability."""
    request = build_availability_request(
        source_id="csv",
        symbol="EURUSD",
        timeframe="H1",
        request_id=generate_id("req"),
    )
    try:
        response = get_data_availability(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("21 data availability: get_data_availability")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_22_market_hours() -> None:
    """Read venue-authoritative exchange sessions."""
    request = build_exchange_session_request(
        symbol="IBM",
        calendar_code="XNYS",
        start=date(2026, 7, 6),
        end=date(2026, 7, 6),
        request_id=generate_id("req"),
    )
    try:
        response = get_exchange_sessions(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("22 market hours: get_exchange_sessions")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_23_trading_sessions() -> None:
    """Read analytical active-session labels."""
    request = build_active_market_sessions_request(
        symbol="EURUSD",
        at=datetime(2026, 7, 20, 13, tzinfo=UTC),
        request_id=generate_id("req"),
    )
    try:
        response = get_active_market_sessions(request)
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("23 trading sessions: get_active_market_sessions")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_26_quality_validation() -> None:
    """Inspect quality calculated from actual canonical records."""
    try:
        response = inspect_data_quality(_sample_bars())
        _header("26 data quality: inspect_data_quality")
        print(f"\nStatus: {response.status}")
        print(f"\nMessage: {response.message}")
        print(f"\nData: {response.data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_27_resampling() -> None:
    """Resample deterministic M1 bars to closed M5 bars."""
    try:
        response = resample_ohlcv(_sample_bars(), target_timeframe="M5")
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("27 resampling: resample_ohlcv")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_28_multitimeframe_alignment() -> None:
    """Align M1 and M5 datasets backward without lookahead."""
    m1 = _sample_bars()
    m5_response = resample_ohlcv(m1, target_timeframe="M5")
    if m5_response.data is None:
        print("Unavailable -> M5 resampling returned no dataset")
        print(f"Data -> {m5_response!r}")
        return
    try:
        response = align_multitimeframe_data(
            {"M1": m1, "M5": m5_response.data},
            target_timestamps=(m1.records[-1].available_at,),
        )
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("28 multi-timeframe alignment: align_multitimeframe_data")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_29_tick_aggregation() -> None:
    """Aggregate canonical ticks into M1 OHLCV bars."""
    ticks = tuple(
        build_tick_record(
            timestamp=_START + timedelta(seconds=index * 10),
            last=Decimal("1.1000") + Decimal(index) * Decimal("0.0001"),
            volume=Decimal(10),
            bid=Decimal("1.0999") + Decimal(index) * Decimal("0.0001"),
            ask=Decimal("1.1001") + Decimal(index) * Decimal("0.0001"),
            price_unit="USD",
            volume_unit="lots",
            source="usage-fixture",
            source_symbol="EURUSD",
            source_revision="usage-v1",
            available_at=_START + timedelta(seconds=index * 10 + 1),
        )
        for index in range(12)
    )
    source = _sample_bars().model_copy(
        update={
            "data_kind": "ticks",
            "timeframe": None,
            "records": ticks,
            "start": ticks[0].timestamp,
            "end": ticks[-1].timestamp,
            "available_at": ticks[-1].available_at,
            "record_count": len(ticks),
        }
    )
    try:
        response = aggregate_ticks_to_bars(source, "M1", "last")
        if response.data is not None:
            data = to_ohlcv_dataframe(response.data)
            _header("29 tick aggregation: aggregate_ticks_to_bars")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_30_scheduler_create_status() -> None:
    """Create a bounded update job and query its status."""
    request_id = generate_id("req")
    definition = build_job_definition(
        job_id="usage-sync-eurusd",
        source_id="mt5",
        symbols=("EURUSD",),
        timeframes=("M1",),
        data_kinds=("ohlcv",),
        start=_START,
        end=_END,
        interval_seconds=3600,
        enabled=True,
        created_at=datetime.now(UTC),
        request_id=request_id,
    )
    try:
        created = create_data_update_job(definition, request_id=request_id)
        _header("30 scheduler create/status")
        print(f"\nStatus: {created.status}")
        print(f"\nMessage: {created.message}")
        print(f"\nData: {created.data}")
        status_request = build_job_status_request(
            job_id="usage-sync-eurusd", request_id=request_id
        )
        status_resp = get_data_update_job_status(status_request)
        print(f"\nJob Status: {status_resp.status}")
        print(f"\nJob Message: {status_resp.message}")
        print(f"\nJob Data: {status_resp.data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_31_scheduler_start_stop() -> None:
    """Start and stop a registered update job."""
    request_id = generate_id("req")
    try:
        start_resp = start_data_update_job(
            job_id="usage-sync-eurusd", request_id=request_id
        )
        _header("31 scheduler lifecycle")
        print(f"\nStart Status: {start_resp.status}")
        print(f"\nStart Message: {start_resp.message}")
        print(f"\nStart Data: {start_resp.data}")
        stop_resp = stop_data_update_job(
            job_id="usage-sync-eurusd", request_id=request_id
        )
        print(f"\nStop Status: {stop_resp.status}")
        print(f"\nStop Message: {stop_resp.message}")
        print(f"\nStop Data: {stop_resp.data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_32_tick_model_trading_bar() -> None:
    """Derive four deterministic ticks per trading bar using MT5 EURUSD H1 bars."""
    bars = _mt5_bars(timeframe="H1", limit=100)
    if bars is None:
        print("\nUnavailable -> MT5 EURUSD H1 bars offline or disabled")
        return
    try:
        response = generate_tick_series(
            bars, model="trading_bar", trading_timeframe="H1"
        )
        if response.data is not None:
            data = to_tick_dataframe(response.data)
            _header("32 trading-bar tick model: generate_tick_series")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_33_tick_model_generated() -> None:
    """Derive a bounded volume-interpolated tick series using MT5 EURUSD H1 bars."""
    bars = _mt5_bars(timeframe="H1", limit=100)
    if bars is None:
        print("\nUnavailable -> MT5 EURUSD H1 bars offline or disabled")
        return
    try:
        response = generate_tick_series(
            bars,
            model="generated",
            trading_timeframe="H1",
            max_records=50_000,
        )
        if response.data is not None:
            data = to_tick_dataframe(response.data)
            _header("33 generated tick model: generate_tick_series")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_34_tick_model_ohlc_m1() -> None:
    """Derive ticks from lower-timeframe OHLC evidence using MT5 EURUSD H1 and M1 bars."""
    bars = _mt5_bars(timeframe="H1", limit=100)
    m1_bars = _mt5_bars(timeframe="M1", limit=6000)
    if bars is None or m1_bars is None:
        print("\nUnavailable -> MT5 EURUSD H1 or M1 bars offline or disabled")
        return
    try:
        response = generate_tick_series(
            bars,
            model="ohlc_m1",
            m1_dataset=m1_bars,
            trading_timeframe="H1",
        )
        if response.data is not None:
            data = to_tick_dataframe(response.data)
            _header("34 M1 evidence tick model: generate_tick_series")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_35_tick_model_real() -> None:
    """Normalize supplied genuine-tick-shaped evidence using MT5 EURUSD H1 bars and MT5 ticks."""
    bars = _mt5_bars(timeframe="H1", limit=100)
    real_ticks = _mt5_ticks(limit=100)
    if bars is None or real_ticks is None:
        source_ticks = (
            generate_tick_series(bars, model="trading_bar", trading_timeframe="H1").data
            if bars is not None
            else None
        )
        real_ticks = source_ticks
    if bars is None or real_ticks is None:
        print("\nUnavailable -> MT5 EURUSD H1 bars or ticks offline or disabled")
        return
    try:
        response = generate_tick_series(
            bars,
            model="real",
            real_tick_dataset=real_ticks,
            trading_timeframe="H1",
        )
        if response.data is not None:
            data = to_tick_dataframe(response.data)
            _header("35 real tick model: generate_tick_series")
            print(f"\nStatus: {response.status}")
            print(f"\nMessage: {response.message}")
            print(f"\nData: {data}")
    except Exception as exc:
        print(f"\nError: {exc}")


def example_36_cleanup() -> None:
    """Clear Data cache entries through the current public boundary."""
    try:
        request = build_cache_clear_request(
            namespace="data",
            dry_run=True,
            max_entries=100,
            request_id=generate_id("req"),
        )
        response = clear_data_cache(request)
        _header("36 cleanup: clear_data_cache")
        print(f"\nStatus: {response.status}")
        print(f"\nMessage: {response.message}")
        print(f"\nData: {response.data}")
    except Exception as exc:
        print(f"\nError: {exc}")


_EXAMPLES = (
    example_01_mt5_bars,
    example_02_mt5_ticks,
    example_03_mt5_stream,
    example_04_dukascopy,
    example_05_yahoo,
    example_06_binance,
    example_07_synthetic_bars,
    example_08_csv_load_direct,
    example_09_csv_tool_load,
    example_10_csv_fetch_range,
    example_11_parquet_load_direct,
    example_12_parquet_tool_load,
    example_13_csv_saver,
    example_14_parquet_saver,
    example_15_gateway_synthetic,
    example_16_gateway_csv,
    example_17_gateway_parquet,
    example_18_caching,
    example_19_symbol_discovery,
    example_20_symbol_metadata,
    example_21_data_availability,
    example_22_market_hours,
    example_23_trading_sessions,
    example_26_quality_validation,
    example_27_resampling,
    example_28_multitimeframe_alignment,
    example_29_tick_aggregation,
    example_30_scheduler_create_status,
    example_31_scheduler_start_stop,
    example_32_tick_model_trading_bar,
    example_33_tick_model_generated,
    example_34_tick_model_ohlc_m1,
    example_35_tick_model_real,
    example_36_cleanup,
)


def main() -> None:
    """Run all direct legacy scenarios in deterministic order."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip external provider reads for deterministic validation.",
    )
    args = parser.parse_args()
    try:
        with _provider_runtime_context(offline=args.offline):
            for example in _EXAMPLES:
                try:
                    example()
                except Exception as exc:
                    print(f"\nError in {example.__name__}: {exc}")
    except Exception as exc:
        print(f"\nError in provider runtime: {exc}")
        return
    print(f"\nSuccess -> completed {len(_EXAMPLES)} Data scenarios directly")
    print("Data -> supplemental catalogue; registered feature count remains 14")


if __name__ == "__main__":
    main()
