"""Run synthetic data generation examples (FEAT-DATA-04)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    SyntheticRequest,
    generate_synthetic_bars,
    generate_synthetic_ticks,
    to_ohlcv_dataframe,
    to_tick_dataframe,
)
from app.utils import generate_id

_START = datetime(2026, 6, 1, tzinfo=UTC)


def example_07_synthetic_bars() -> None:
    """Generate deterministic synthetic OHLCV bars."""
    req_id = generate_id("req")
    req = SyntheticRequest(
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
        request_id=req_id,
    )
    dataset = generate_synthetic_bars(req)
    print(f"Synthetic bar rows: {dataset.record_count} symbol={dataset.symbol}")
    print(to_ohlcv_dataframe(dataset))


def example_synthetic_ticks() -> None:
    """Generate deterministic synthetic tick records."""
    req_id = generate_id("req")
    req = SyntheticRequest(
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
        request_id=req_id,
    )
    dataset = generate_synthetic_ticks(req)
    print(f"Synthetic tick rows: {dataset.record_count} symbol={dataset.symbol}")
    print(to_tick_dataframe(dataset))


def _demonstrate_feature() -> None:
    """Run all synthetic data generation examples."""
    example_07_synthetic_bars()
    example_synthetic_ticks()


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_039() -> None:
    "FR-DATA-039: Generate bounded canonical bars or ticks with GBM, exact parameters, and deterministic output when a seed is supplied; generation is not a source adapter."  # noqa: E501 - exact specification text
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (fr_data_039,)
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
