"""Demonstrate FEAT-DATA-05 tick-series derivation models."""

from __future__ import annotations

import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_data_settings,
    build_market_data_request,
    generate_tick_series,
    generate_tick_series_to_parquet,
    get_market_data,
    get_tick_data,
    to_ohlcv_dataframe,
    to_tick_dataframe,
)
from app.services.data.contracts.errors import DataError
from app.utils import generate_id

_START = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
_END = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _approved_temporary_directory(
    settings: Any | None = None,
) -> TemporaryDirectory[str]:
    """Create an automatically cleaned directory under an approved Data root."""
    approved_root = (settings or build_data_settings()).approved_storage_roots[0]
    approved_root.mkdir(parents=True, exist_ok=True)
    return TemporaryDirectory(dir=approved_root)


def _print_header(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 100)
    print(f"\t\t {title} ")


def _sample_bars(
    timeframe: str = "H1",
    *,
    limit: int = 100,
) -> Any | None:
    """Retrieve a bounded MT5 bar dataset for the requested timeframe."""
    req_id = generate_id("req")
    req = build_market_data_request(
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
        request_id=req_id,
    )
    try:
        response = get_market_data(req)
        if response.status == "success" and response.data is not None:
            _print_quality(f"MT5 {timeframe} bars", response.data)
            return response.data
        return None
    except DataError as exc:
        print(f"MT5 example handled: {exc.code}")
        return None


def _sample_ticks() -> Any | None:
    """Retrieve MT5 tick dataset via public get_tick_data."""
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
            _print_quality("MT5 ticks", response.data)
            return response.data
        return None
    except DataError as exc:
        print(f"MT5 Ticks example handled: {exc.code}")
        return None


def _print_quality(label: str, dataset: Any) -> None:
    """Print bounded quality evidence returned with a market dataset."""
    report = dataset.quality_report
    issue_codes = sorted({issue.code for issue in report.issues})
    print(
        f"{label}: records={dataset.record_count}, "
        f"quality={report.quality_status}, score={report.quality_score}"
    )
    if issue_codes:
        print(f"Quality issues: {', '.join(issue_codes)}")
    if report.warnings:
        print(f"Quality warnings: {', '.join(report.warnings)}")


def _print_generation_rate(record_count: int, elapsed_seconds: float) -> None:
    """Print bounded throughput evidence for one derivation call."""
    rate = record_count / max(elapsed_seconds, 1e-9)
    print(
        f"Generated {record_count:,} ticks in {elapsed_seconds:.4f} seconds "
        f"({rate:,.0f} ticks/second)"
    )


def example_01_tick_model_trading_bar() -> None:
    """Generate four ticks per trading timeframe bar using trading_bar model."""
    _header("Generate four ticks per trading timeframe bar using trading_bar model.")
    bars = _sample_bars()
    if bars is None:
        return
    start_time = time.perf_counter()
    ticks_res = generate_tick_series(bars, model="trading_bar", trading_timeframe="H1")
    end_time = time.perf_counter()
    if ticks_res.status == "success" and ticks_res.data is not None:
        ticks = ticks_res.data
        _print_generation_rate(ticks.record_count, end_time - start_time)
        print(f"Original Data: {bars.symbol} records={bars.record_count}")
        print(to_ohlcv_dataframe(bars))
        print(f"Generated Ticks: {ticks.symbol} records={ticks.record_count}")
        _print_quality("Generated trading_bar ticks", ticks)
        print(to_tick_dataframe(ticks))


def example_02_tick_model_generated() -> None:
    """Generate interpolated ticks from bar volume using generated model."""
    _header("Generate interpolated ticks from bar volume using generated model.")
    bars = _sample_bars(limit=5)
    if bars is None:
        return
    start_time = time.perf_counter()
    ticks_res = generate_tick_series(
        bars,
        model="generated",
        trading_timeframe="H1",
        max_records=50_000,
    )
    end_time = time.perf_counter()
    if ticks_res.status == "success" and ticks_res.data is not None:
        ticks = ticks_res.data
        _print_generation_rate(ticks.record_count, end_time - start_time)
        print(f"Original Data: {bars.symbol} records={bars.record_count}")
        print(to_ohlcv_dataframe(bars))
        print(f"Generated Ticks: {ticks.symbol} records={ticks.record_count}")
        _print_quality("Generated volume-derived ticks", ticks)
        print(to_tick_dataframe(ticks))


def example_03_tick_model_ohlc_m1() -> None:
    """Generate four ticks per real M1 bar."""
    _header("Generate four ticks per real M1 bar.")
    bars = _sample_bars()
    m1_bars = _sample_bars(timeframe="M1")
    if bars is None or m1_bars is None:
        return

    try:
        start_time = time.perf_counter()
        ticks_res = generate_tick_series(
            bars,
            model="ohlc_m1",
            m1_dataset=m1_bars,
            trading_timeframe="H1",
        )
        end_time = time.perf_counter()
        if ticks_res.status == "success" and ticks_res.data is not None:
            ticks = ticks_res.data
            _print_generation_rate(ticks.record_count, end_time - start_time)
            print(f"Original Data: {bars.symbol} records={bars.record_count}")
            print(to_ohlcv_dataframe(m1_bars))
            print(f"Generated Ticks: {ticks.symbol} records={ticks.record_count}")
            _print_quality("Generated ohlc_m1 ticks", ticks)
            print(to_tick_dataframe(ticks))
    except DataError as exc:
        print(f"ohlc_m1 tick model handled: {exc.code}")


def example_04_tick_model_real() -> None:
    """Standardize provider ticks and annotate their H1 bucket positions."""
    _header("Standardize provider ticks and annotate their H1 bucket positions.")
    bars = _sample_bars()
    ticks_data = _sample_ticks()
    if bars is None or ticks_data is None:
        return
    try:
        start_time = time.perf_counter()
        ticks_res = generate_tick_series(
            bars,
            model="real",
            real_tick_dataset=ticks_data,
            trading_timeframe="H1",
        )
        end_time = time.perf_counter()
        if ticks_res.status == "success" and ticks_res.data is not None:
            ticks = ticks_res.data
            _print_generation_rate(ticks.record_count, end_time - start_time)
            print(f"Original Data: {bars.symbol} records={bars.record_count}")
            print(to_ohlcv_dataframe(bars))
            print(
                f"Original Ticks Data: {ticks_data.symbol} "
                f"records={ticks_data.record_count}"
            )
            print(to_tick_dataframe(ticks_data))
            print(f"Generated Ticks: {ticks.symbol} records={ticks.record_count}")
            _print_quality("Standardized real ticks", ticks)
            print(to_tick_dataframe(ticks))
    except DataError as exc:
        print(f"real tick model handled: {exc.code}")


def example_05_stream_tick_series_to_parquet() -> None:
    """Write a bounded generated tick series through the public Parquet API."""
    _header("Write a bounded generated tick series through the public Parquet API.")
    bars = _sample_bars(limit=5)
    if bars is None:
        return

    with _approved_temporary_directory() as temporary_directory:
        start_time = time.perf_counter()
        dest_path = Path("data/raw/ticks.parquet")
        res = generate_tick_series_to_parquet(
            bars,
            path=dest_path,
            model="trading_bar",
            trading_timeframe="H1",
        )
        end_time = time.perf_counter()
        if res.status == "success" and res.data is not None:
            metadata = res.data
            _print_generation_rate(metadata.record_count, end_time - start_time)
            print(
                f"Wrote Parquet artifact: path={metadata.path} "
                f"records={metadata.record_count} bytes={metadata.byte_size}"
            )


def fr_data_005() -> None:
    _print_header("FEAT-DATA-05 Tick Derivation Surface")
    example_01_tick_model_trading_bar()
    example_02_tick_model_generated()
    example_03_tick_model_ohlc_m1()
    example_04_tick_model_real()
    example_05_stream_tick_series_to_parquet()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    fr_data_005()


if __name__ == "__main__":
    main()
