"""Executable Simulation timeline usage example.

Demonstrates tick contract construction, tick timeline building, and intent timing validation.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    TickRecord,
)
from app.services.simulator.timeline import (
    Tick,
    build_tick_timeline,
    validate_intent_timing,
)


def _dataset() -> MarketDataset:
    """Build tick dataset for timeline example."""
    start = datetime(2025, 1, 1, tzinfo=UTC)
    t2 = start + timedelta(seconds=1)
    r1 = TickRecord(
        timestamp=start,
        source="fixture",
        source_symbol="EURUSD",
        available_at=start,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        last=Decimal("1.10001"),
        volume=Decimal(1),
        price_unit="quote",
        volume_unit="lot",
        source_bar_time=start,
        tick_index_in_bar=0,
        bar_phase=1,
    )
    r2 = TickRecord(
        timestamp=t2,
        source="fixture",
        source_symbol="EURUSD",
        available_at=t2,
        bid=Decimal("1.10005"),
        ask=Decimal("1.10007"),
        last=Decimal("1.10006"),
        volume=Decimal(1),
        price_unit="quote",
        volume_unit="lot",
        source_bar_time=t2,
        tick_index_in_bar=1,
        bar_phase=1,
    )
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=2,
        checked_count=2,
        truncated=False,
        sample_limit=2,
        schema_version="v1",
        generated_at=t2,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        timeframe="M1",
        records=(r1, r2),
        start=start,
        end=t2,
        available_at=t2,
        record_count=2,
        quality_report=quality,
        source_metadata={"tick_generation_model": "real"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-11111111-1111-4111-8111-111111111111",
    )


def example_timeline() -> None:
    """Demonstrate timeline and tick operations."""
    print("=" * 80)
    print("Simulator Example 3: Tick Contract and Timeline")
    print("=" * 80)

    instant = datetime(2025, 1, 1, tzinfo=UTC)

    # 1. Tick contract
    tick = Tick(
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        source_id="provider",
        sequence=0,
        available_at=instant,
    )
    print(f"Tick spread: {tick.ask - tick.bid}")

    # 2. Build tick timeline
    timeline = build_tick_timeline(_dataset())
    sequences = tuple(t.sequence for t in timeline)
    print(f"Timeline tick sequences: {sequences}")

    # 3. Validate intent timing
    validate_intent_timing(instant, instant)
    print("Intent timing validated successfully")


def main() -> None:
    """Run Simulator timeline usage example."""
    example_timeline()


if __name__ == "__main__":
    main()
