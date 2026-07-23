"""Run synthetic data generation examples (FEAT-DATA-04)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.synthetic_data import (
    generate_synthetic_bars,
    generate_synthetic_ticks,
)
from app.services.data.synthetic_data.contracts import SyntheticRequest
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
        },
        precision_policy="decimal_string",
        request_id=req_id,
    )
    dataset = generate_synthetic_bars(req)
    print(f"Synthetic bar rows: {dataset.record_count} symbol={dataset.symbol}")


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


def main() -> None:
    """Run all synthetic data generation examples."""
    example_07_synthetic_bars()
    example_synthetic_ticks()


if __name__ == "__main__":
    main()
