# ruff: noqa: BLE001
"""Run synthetic data generation examples (FEAT-DATA-04)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import (
    build_synthetic_request,
    generate_synthetic_bars,
    generate_synthetic_ticks,
    to_ohlcv_dataframe,
    to_tick_dataframe,
)

_START = datetime(2026, 6, 1, tzinfo=UTC)


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


def fr_data_039_request() -> None:
    """FR-DATA-039: Stage 1 — Construct SyntheticRequest parameters including explicit seed for deterministic replay."""
    _header("Stage 1: Synthetic Request Construction - Synthetic Request (FR-DATA-039)")
    req = build_synthetic_request(
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
    print(_format_result(req))
    print(
        f"Data -> SyntheticRequest(symbol={req.symbol}, kind={req.data_kind}, seed={req.seed})"
    )


def fr_data_039_bars() -> None:
    """FR-DATA-039: Stage 2 — Generate deterministic synthetic OHLCV bars using GBM algorithm and seeded parameters."""
    _header("Stage 2: Synthetic Bar Generation - Generate Synthetic Bars (FR-DATA-039)")
    req = build_synthetic_request(
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
            "spread_min": Decimal(10),
            "spread_max": Decimal(50),
        },
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    try:
        response = generate_synthetic_bars(req)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            dataset = response.data
            print(
                f"Data -> MarketDataset(symbol={dataset.symbol}, records={dataset.record_count})"
            )
            frame = to_ohlcv_dataframe(dataset)
            print(f"Data -> DataFrame shape={frame.shape}")
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_039_ticks() -> None:
    """FR-DATA-039: Stage 3 — Generate deterministic synthetic tick records with intra-bar timing and spread dynamics."""
    _header(
        "Stage 3: Synthetic Tick Generation - Generate Synthetic Ticks (FR-DATA-039)"
    )
    req = build_synthetic_request(
        symbol="GBPUSD",
        data_kind="ticks",
        start=_START,
        record_count=50,
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
        response = generate_synthetic_ticks(req)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            dataset = response.data
            print(
                f"Data -> MarketDataset(symbol={dataset.symbol}, records={dataset.record_count})"
            )
            frame = to_tick_dataframe(dataset)
            print(f"Data -> DataFrame shape={frame.shape}")
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def main() -> None:
    """Execute every functional-requirement demonstration."""
    print("=" * 80)
    print("FEATURE: FEAT-DATA-04 - Synthetic Data Generation")
    print(
        "PURPOSE: SyntheticRequest, seeded randomness, synthetic bar/tick generation, and provenance"
    )
    print(
        "MODULE FLOW: Stage 1 (Synthetic Request Construction) -> Stage 2 (Synthetic Bar Generation) -> Stage 3 (Synthetic Tick Generation)"
    )
    print("=" * 80)

    fr_data_039_request()
    fr_data_039_bars()
    fr_data_039_ticks()
    print("SUCCESS: FEAT-DATA-04 completed")


if __name__ == "__main__":
    main()
