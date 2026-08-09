"""Standalone usage for FEAT-SIM-12 execution realism."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    build_fill_model_provider,
    build_latency_profile,
    build_queue_model,
    price_realistic_execution,
    project_execution_views,
    project_latency_timestamps,
    resolve_cancel_replace_race,
    simulate_queue_fill,
)


def _latency() -> object:
    """Build one bounded latency profile."""
    return build_latency_profile(network_ms=Decimal(2), venue_ms=Decimal(3))


def fr_sim_118() -> None:
    """FR-SIM-118: Simulator shall validate non-negative deterministic market, client, network, broker, venue, report, and processing latency and project their complete causal timestamp chain."""
    projected = project_latency_timestamps(datetime.now(UTC), _latency())
    print(f"SUCCESS: FR-SIM-118 latency projected; Data -> {tuple(projected)}")


def fr_sim_119() -> None:
    """FR-SIM-119: Simulator shall model price level, order quantity, quantity ahead, cancellation rate, traded volume, remaining queue position, and bounded fill probability."""
    queue = build_queue_model(
        price=Decimal("1.1"),
        order_quantity=Decimal(2),
        quantity_ahead=Decimal(1),
        cancellation_rate=Decimal(0),
        maximum_fill_probability=Decimal(1),
    )
    result = simulate_queue_fill(queue, traded_volume=Decimal(2))
    print(f"SUCCESS: FR-SIM-119 queue modeled; Data -> fill={result.filled_quantity}")


def fr_sim_120() -> None:
    """FR-SIM-120: Simulator shall calculate finite Decimal adverse slippage and linear market impact within an explicit maximum movement ceiling."""
    result = price_realistic_execution(
        side="BUY",
        base_price=Decimal("1.1"),
        quantity=Decimal(2),
        point_value=Decimal("0.0001"),
        price_quantum=Decimal("0.00001"),
        fixed_slippage_points=Decimal(1),
        impact_points_per_unit=Decimal("0.5"),
        maximum_total_points=Decimal(3),
        latency=_latency(),
    )
    print(f"SUCCESS: FR-SIM-120 price modeled; Data -> {result.execution_price}")


def fr_sim_121() -> None:
    """FR-SIM-121: Simulator shall resolve cancel, replace, and fill races by aware venue timestamps with an explicit fill-before-cancel-before-replace tie priority."""
    now = datetime.now(UTC)
    result = resolve_cancel_replace_race(fill_at=now, cancel_at=now, replace_at=None)
    print(f"SUCCESS: FR-SIM-121 race resolved; Data -> {result['winner']}")


def fr_sim_122() -> None:
    """FR-SIM-122: Simulator shall separate venue-effective state from player-perceived state and expose no event before its perception timestamp."""
    now = datetime.now(UTC)
    views = project_execution_views(
        (
            {
                "event_id": "e",
                "venue_at": now,
                "perceived_at": now + timedelta(seconds=1),
            },
        ),
        as_of=now,
    )
    print(
        f"SUCCESS: FR-SIM-122 views separated; Data -> venue={len(views['venue'])}, player={len(views['player'])}"
    )


def fr_sim_123() -> None:
    """FR-SIM-123: Simulator shall provide explicit instrument and market-data-bound fill-model calibration evidence to Optimization without inferred defaults."""
    provider = build_fill_model_provider(
        {"EURUSD": {"market_data_ref": "dataset-usage", "latency_ms": 5}}
    )
    evidence = provider.fill_model_calibration(
        market_data_ref="dataset-usage", instrument="EURUSD"
    )
    print(f"SUCCESS: FR-SIM-123 provider built; Data -> {evidence['status']}")


def main() -> None:
    """Run every FEAT-SIM-12 requirement demonstration."""
    print("FEATURE: FEAT-SIM-12 — Execution Realism Models")
    fr_sim_118()
    fr_sim_119()
    fr_sim_120()
    fr_sim_121()
    fr_sim_122()
    fr_sim_123()


if __name__ == "__main__":
    main()
