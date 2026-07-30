"""Executable Simulation timeline usage example.

Demonstrates tick contract construction, tick timeline building, and intent
timing validation.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_data_quality_report,
    build_market_dataset,
    build_tick_record,
)
from app.services.simulator import (
    build_tick_timeline,
    create_simulation_value,
    dump_simulation_value,
    unwrap_simulation_response,
    validate_intent_timing,
)


def _value(response: object) -> object:
    """Unwrap one public Simulation response for display."""
    return unwrap_simulation_response(response, operation="usage.timeline")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _dataset() -> object:
    """Build tick dataset for timeline example."""
    start = datetime(2025, 1, 1, tzinfo=UTC)
    t2 = start + timedelta(seconds=1)
    r1 = build_tick_record(
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
    r2 = build_tick_record(
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
    quality = build_data_quality_report(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=2,
        checked_count=2,
        truncated=False,
        sample_limit=2,
        schema_version="v1",
        generated_at=t2,
    )
    return build_market_dataset(
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


def fr_sim_004() -> None:
    """Demonstrate FR-SIM-004.

    Responsibility:
        The system shall expose an immutable UTC tick containing symbol, timestamp, bid,
        ask, source identity, sequence, and availability metadata with finite positive
        prices and `ask >= bid`.
    """
    _header(
        "Demonstrate FR-SIM-004. Responsibility: The system shall expose an immutable UTC tick containing symbol, timestamp, bid, ask, source identity, sequence, and availability metadata with finite positive prices and `ask >= bid`."
    )
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    tick = create_simulation_value(
        "Tick",
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        source_id="provider",
        sequence=0,
        available_at=instant,
    )
    print("Validated immutable tick:", dump_simulation_value(tick))


def fr_sim_005() -> None:
    """Demonstrate FR-SIM-005.

    Responsibility:
        The system shall convert one Data-owned tick `MarketDataset` into a strictly
        ordered immutable `Tick` tuple, validating UTC monotonicity, positive finite
        prices, `ask >= bid`, and the presence of intra-bar phase evidence. Tick
        derivation itself belongs to Data (`FR-DATA-087`-`FR-DATA-090`); Simulation
        constructs no ticks, applies no spread model, and consumes no seed.
    """
    _header(
        "Demonstrate FR-SIM-005. Responsibility: The system shall convert one Data-owned tick `MarketDataset` into a strictly ordered immutable `Tick` tuple, validating UTC monotonicity, positive finite prices, `ask >= bid`, and the presence of intra-bar phase evidence. Tick derivation itself belongs to Data (`FR-DATA-087`-`FR-DATA-090`); Simulation constructs no ticks, applies no spread model, and consumes no seed."
    )
    timeline = _value(build_tick_timeline(_dataset()))
    rows = tuple(dump_simulation_value(tick) for tick in timeline)
    print("Ordered execution timeline:", rows)


def fr_sim_006() -> None:
    """Demonstrate FR-SIM-006.

    Responsibility:
        The system shall reject a strategy intent whose evidence became available after
        its execution time and enforce previous-closed-bar visibility by default.
    """
    _header(
        "Demonstrate FR-SIM-006. Responsibility: The system shall reject a strategy intent whose evidence became available after its execution time and enforce previous-closed-bar visibility by default."
    )
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    _value(validate_intent_timing(instant, instant))
    print("Intent timing decision:", {"visible_at": instant, "execution_at": instant})


def main() -> None:
    """Run Simulator timeline usage example."""
    fr_sim_004()
    fr_sim_005()
    fr_sim_006()


if __name__ == "__main__":
    main()
