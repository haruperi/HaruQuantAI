"""Demonstrate FEAT-DATA-05 tick-series derivation models."""

from __future__ import annotations

import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.services.data import (
    DataError,
    DataSettings,
    MarketDataRequest,
    MarketDataset,
    generate_tick_series,
    generate_tick_series_to_parquet,
    get_market_data,
    get_tick_data,
    to_ohlcv_dataframe,
    to_tick_dataframe,
)
from app.utils import generate_id

_START = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
_END = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)


def _approved_temporary_directory(
    settings: DataSettings | None = None,
) -> TemporaryDirectory[str]:
    """Create an automatically cleaned directory under an approved Data root."""
    approved_root = (settings or DataSettings()).approved_storage_roots[0]
    approved_root.mkdir(parents=True, exist_ok=True)
    return TemporaryDirectory(dir=approved_root)


def _print_header(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 100)
    print(f"\t\t {title} ")
    print("=" * 100)


def _sample_bars(
    timeframe: str = "H1",
    *,
    limit: int = 100,
) -> MarketDataset | None:
    """Retrieve a bounded MT5 bar dataset for the requested timeframe."""
    req_id = generate_id("req")
    req = MarketDataRequest(
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
        dataset = get_market_data(req)
        _print_quality(f"MT5 {timeframe} bars", dataset)
        return dataset
    except DataError as exc:
        print(f"MT5 example handled: {exc.code}")
        return None


def _sample_ticks() -> MarketDataset | None:
    """Retrieve MT5 tick dataset via public get_tick_data."""
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
        dataset = get_tick_data(req)
        _print_quality("MT5 ticks", dataset)
        return dataset
    except DataError as exc:
        print(f"MT5 Ticks example handled: {exc.code}")
        return None


def _print_quality(label: str, dataset: MarketDataset) -> None:
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
    _print_header("EXAMPLE 01: Generate four ticks per trading timeframe bar")
    bars = _sample_bars()
    if bars is None:
        return
    start_time = time.perf_counter()
    ticks = generate_tick_series(bars, model="trading_bar", trading_timeframe="H1")
    end_time = time.perf_counter()
    _print_generation_rate(ticks.record_count, end_time - start_time)
    print(f"Original Data: {bars.symbol} records={bars.record_count}")
    print(to_ohlcv_dataframe(bars))
    print(f"Generated Ticks: {ticks.symbol} records={ticks.record_count}")
    _print_quality("Generated trading_bar ticks", ticks)
    print(to_tick_dataframe(ticks))


def example_02_tick_model_generated() -> None:
    """Generate interpolated ticks from bar volume using generated model."""
    _print_header("EXAMPLE 02: Generate interpolated ticks from bar volume")
    bars = _sample_bars(limit=5)
    if bars is None:
        return
    start_time = time.perf_counter()
    ticks = generate_tick_series(
        bars,
        model="generated",
        trading_timeframe="H1",
        max_records=50_000,
    )
    end_time = time.perf_counter()
    _print_generation_rate(ticks.record_count, end_time - start_time)
    print(f"Original Data: {bars.symbol} records={bars.record_count}")
    print(to_ohlcv_dataframe(bars))
    print(f"Generated Ticks: {ticks.symbol} records={ticks.record_count}")
    _print_quality("Generated volume-derived ticks", ticks)
    print(to_tick_dataframe(ticks))


def example_03_tick_model_ohlc_m1() -> None:
    """Generate four ticks per real M1 bar."""
    _print_header("EXAMPLE 03: Generate OHLC ticks from real M1 bars")
    bars = _sample_bars()
    m1_bars = _sample_bars(timeframe="M1")
    if bars is None or m1_bars is None:
        return

    try:
        start_time = time.perf_counter()
        ticks = generate_tick_series(
            bars,
            model="ohlc_m1",
            m1_dataset=m1_bars,
            trading_timeframe="H1",
        )
        end_time = time.perf_counter()
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
    _print_header("EXAMPLE 04: Standardize real provider ticks")
    bars = _sample_bars()
    ticks_data = _sample_ticks()
    if bars is None or ticks_data is None:
        return
    try:
        start_time = time.perf_counter()
        ticks = generate_tick_series(
            bars,
            model="real",
            real_tick_dataset=ticks_data,
            trading_timeframe="H1",
        )
        end_time = time.perf_counter()
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
    _print_header("EXAMPLE 05: Stream generated ticks to Parquet")
    bars = _sample_bars(limit=5)
    if bars is None:
        return

    with _approved_temporary_directory() as temporary_directory:
        start_time = time.perf_counter()
        artifact = generate_tick_series_to_parquet(
            bars,
            path=Path(temporary_directory) / "generated_ticks.parquet",
            max_output_rows_per_chunk=50_000,
            model="generated",
            trading_timeframe="H1",
            max_records=50_000,
            price_precision=8,
        )
        elapsed_seconds = time.perf_counter() - start_time
        _print_generation_rate(int(artifact["rows"]), elapsed_seconds)
        print(
            "Parquet artifact: "
            f"rows={artifact['rows']}, columns={len(artifact['columns'])}, "
            f"exists={Path(str(artifact['path'])).is_file()}"
        )


def _demonstrate_feature() -> None:
    """Run all tick derivation model examples."""
    example_01_tick_model_trading_bar()
    example_02_tick_model_generated()
    example_03_tick_model_ohlc_m1()
    example_04_tick_model_real()
    example_05_stream_tick_series_to_parquet()


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_087() -> None:
    "FR-DATA-087: Derive a canonical tick `MarketDataset` from real bar or tick evidence using exactly one approved model, preserving real prices and real tick counts, ordering ticks strictly by UTC timestamp then intra-bar index, and quantizing every price to `Decimal` at the contract boundary. Exact fixed-point arrays may be used internally; no array value crosses the canonical boundary."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_088() -> None:
    "FR-DATA-088: Apply exactly one approved spread model to every generated tick: `native_spread` uses the provider-reported spread, `fixed_spread` applies one configured point value, and `variable_spread` draws bounded points from a seeded generator. A `variable_spread` request without a seed fails; identical seed and inputs reproduce identical spreads."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_089() -> None:
    "FR-DATA-089: Attach deterministic intra-bar position evidence to every generated tick: `source_bar_time`, `tick_index_in_bar`, and a phase bitmask marking the bar open, high, low, and close observations. The bitmask carries no trading meaning and never encodes an order, signal, or decision."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_090() -> None:
    "FR-DATA-090: Stream a generated tick series to a bounded Parquet artifact under an approved root with output-aware chunking, returning path, row count, and column names without holding the full series in memory. Eligible fixed-point chunks bypass canonical in-memory record materialization."  # noqa: E501 - exact specification text
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_087,
        fr_data_088,
        fr_data_089,
        fr_data_090,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
