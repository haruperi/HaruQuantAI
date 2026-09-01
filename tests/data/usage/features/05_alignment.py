"""Demonstrate FEAT-DATA-05 backward-only dataset alignment."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import (
    align_datasets,
    align_multitimeframe_data,
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
)


def _dataset(*, symbol: str, minute_offset: int) -> Any:
    """Build one bounded genuine-evidence-shaped dataset.

    Args:
        symbol: Source symbol for the example dataset.
        minute_offset: Timestamp offset from the fixed example origin.

    Returns:
        An immutable canonical market dataset.
    """
    timestamp = datetime(2026, 8, 10, 8, minute_offset, tzinfo=UTC)
    record = build_ohlcv_record(
        timestamp=timestamp,
        open=Decimal(100),
        high=Decimal(101),
        low=Decimal(99),
        close=Decimal("100.5"),
        volume=Decimal(10),
        price_unit="USD",
        volume_unit="units",
        source="usage-fixture",
        source_symbol=symbol,
        available_at=timestamp + timedelta(seconds=1),
    )
    quality = build_data_quality_report(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=1,
        checked_count=1,
        truncated=False,
        sample_limit=1,
        schema_version="v1",
        generated_at=record.available_at,
    )
    return build_market_dataset(
        normalization_version="v1",
        data_kind="bars",
        symbol=symbol,
        timeframe="M1",
        records=(record,),
        start=timestamp,
        end=timestamp,
        available_at=record.available_at,
        record_count=1,
        quality_report=quality,
        source_metadata={"source": "usage-fixture"},
        license_metadata={"license": "fixture"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def main() -> None:
    """Run both public alignment operations with bounded deterministic data."""
    eurusd = _dataset(symbol="EURUSD", minute_offset=0)
    gbpusd = _dataset(symbol="GBPUSD", minute_offset=1)
    target = gbpusd.records[0].available_at
    pair_result = align_datasets(
        {"EURUSD": eurusd, "GBPUSD": gbpusd},
        (target,),
    )
    timeframe_result = align_multitimeframe_data(
        {"M1": eurusd},
        target_timestamps=(target,),
    )
    print(
        "DATA SUCCESS: FEAT-DATA-05 alignment",
        pair_result.status,
        timeframe_result.status,
    )


if __name__ == "__main__":
    main()
