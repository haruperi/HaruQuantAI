# ruff: noqa: BLE001
"""Demonstrate FEAT-DATA-05 tick-series derivation models."""

from __future__ import annotations

import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_synthetic_request,
    data_settings_context,
    generate_synthetic_bars,
    generate_tick_series,
    generate_tick_series_to_parquet,
    run_data_migrations,
    to_tick_dataframe,
)
from app.utils import generate_id

_START = datetime(2026, 6, 1, tzinfo=UTC)


@contextmanager
def _approved_temporary_directory(settings: object) -> Iterator[str]:
    """Create a temporary directory beneath the first approved storage root."""
    roots = getattr(settings, "approved_storage_roots", ())
    if not roots:
        raise ValueError("approved_storage_roots must not be empty")
    root = Path(roots[0]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix="usage-tick-derivation-",
        dir=root,
    ) as directory:
        yield directory


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


def _get_synthetic_bars(count: int = 10, timeframe: str = "H1") -> Any:
    """Helper to construct synthetic bars for tick derivation input."""
    req = build_synthetic_request(
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
    res = generate_synthetic_bars(req)
    if res.data is None:
        raise RuntimeError("Failed to build synthetic bars")
    return res.data


def fr_data_087() -> None:
    """FR-DATA-087: Stage 1 — Derive tick series using the `trading_bar` model (4 ticks per bar: open, low/high, high/low, close)."""
    _header("Stage 1: Trading-Bar Model Derivation - trading_bar Model (FR-DATA-087)")
    bars = _get_synthetic_bars(count=5, timeframe="H1")
    t0 = time.perf_counter()
    res = generate_tick_series(bars, model="trading_bar", trading_timeframe="H1")
    t1 = time.perf_counter()
    print(_format_result(res))
    if res.status == "success" and res.data is not None:
        ticks = res.data
        print(
            f"Data -> MarketDataset(symbol={ticks.symbol}, count={ticks.record_count}, elapsed={t1 - t0:.4f}s)"
        )
        frame = to_tick_dataframe(ticks)
        print(f"Data -> Tick DataFrame shape={frame.shape}")


def fr_data_088() -> None:
    """FR-DATA-088: Stage 2 — Derive tick series using the `generated` model (volume-interpolated tick generation)."""
    _header("Stage 2: Generated Model Derivation - generated Model (FR-DATA-088)")
    bars = _get_synthetic_bars(count=5, timeframe="H1")
    t0 = time.perf_counter()
    res = generate_tick_series(
        bars,
        model="generated",
        trading_timeframe="H1",
        max_records=50_000,
    )
    t1 = time.perf_counter()
    print(_format_result(res))
    if res.status == "success" and res.data is not None:
        ticks = res.data
        print(
            f"Data -> MarketDataset(symbol={ticks.symbol}, count={ticks.record_count}, elapsed={t1 - t0:.4f}s)"
        )
        frame = to_tick_dataframe(ticks)
        print(f"Data -> Tick DataFrame shape={frame.shape}")


def fr_data_089() -> None:
    """FR-DATA-089: Stage 3 — Derive tick series using the `ohlc_m1` model (4 ticks per real M1 bar)."""
    _header("Stage 3: OHLC M1 Model Derivation - ohlc_m1 Model (FR-DATA-089)")
    bars = _get_synthetic_bars(count=5, timeframe="H1")
    m1_bars = _get_synthetic_bars(count=300, timeframe="M1")
    try:
        t0 = time.perf_counter()
        res = generate_tick_series(
            bars,
            model="ohlc_m1",
            m1_dataset=m1_bars,
            trading_timeframe="H1",
        )
        t1 = time.perf_counter()
        print(_format_result(res))
        if res.status == "success" and res.data is not None:
            ticks = res.data
            print(
                f"Data -> MarketDataset(symbol={ticks.symbol}, count={ticks.record_count}, elapsed={t1 - t0:.4f}s)"
            )
            frame = to_tick_dataframe(ticks)
            print(f"Data -> Tick DataFrame shape={frame.shape}")
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_090() -> None:
    """FR-DATA-090: Stage 4 — Standardize real provider ticks using the `real` tick model and annotate H1 bucket phase."""
    _header("Stage 4: Real Model Standardization - real Model (FR-DATA-090)")
    bars = _get_synthetic_bars(count=5, timeframe="H1")
    ticks_in = generate_tick_series(
        bars, model="trading_bar", trading_timeframe="H1"
    ).data
    if ticks_in is None:
        print("Data -> Failed to generate source ticks")
        return
    try:
        t0 = time.perf_counter()
        res = generate_tick_series(
            bars,
            model="real",
            real_tick_dataset=ticks_in,
            trading_timeframe="H1",
        )
        t1 = time.perf_counter()
        print(_format_result(res))
        if res.status == "success" and res.data is not None:
            ticks = res.data
            print(
                f"Data -> MarketDataset(symbol={ticks.symbol}, count={ticks.record_count}, elapsed={t1 - t0:.4f}s)"
            )
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_087_090_parquet(directory: Path) -> None:
    """FR-DATA-087..090: Stage 5 — Stream derived tick series directly to a versioned Parquet artifact with manifest."""
    _header(
        "Stage 5: Parquet Artifact Generation - Direct Parquet Output (FR-DATA-087..090)"
    )
    bars = _get_synthetic_bars(count=5, timeframe="H1")
    dest_path = directory / "data" / "raw" / "derived_ticks.parquet"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    res = generate_tick_series_to_parquet(
        bars,
        path=dest_path,
        model="trading_bar",
        trading_timeframe="H1",
    )
    t1 = time.perf_counter()
    print(_format_result(res))
    if res.status == "success" and res.data is not None:
        meta = res.data
        print(
            f"Data -> ParquetArtifact(path={meta.get('path')}, rows={meta.get('rows')}, elapsed={t1 - t0:.4f}s)"
        )


def main() -> None:
    """Execute every functional-requirement demonstration."""
    with TemporaryDirectory(prefix="usage-tick-derivation-") as directory:
        base_dir = Path(directory)
        settings = build_data_settings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=base_dir,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
            ),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            print("=" * 80)
            print("FEATURE: FEAT-DATA-05 - Tick-Series Derivation")
            print(
                "PURPOSE: TickSeriesRequest, fixed-point kernels, derived tick/Parquet operations, and provenance"
            )
            print(
                "MODULE FLOW: Stage 1 (Trading-Bar Model) -> Stage 2 (Generated Model) -> Stage 3 (OHLC M1 Model) -> Stage 4 (Real Model Standardization) -> Stage 5 (Parquet Artifact Generation)"
            )
            print("=" * 80)

            fr_data_087()
            fr_data_088()
            fr_data_089()
            fr_data_090()
            fr_data_087_090_parquet(base_dir)
            print("SUCCESS: FEAT-DATA-05 completed")


if __name__ == "__main__":
    main()
