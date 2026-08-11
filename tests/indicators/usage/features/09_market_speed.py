"""Standalone usage evidence for FEAT-INDI-09."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.indicators.usage._migration_support import run_requirement


def fr_indi_064() -> None:
    """FR-INDI-064: Demonstrate log-price velocity."""
    run_requirement("FR-INDI-064", "price_velocity", {"k": 2, "unit_seconds": 300.0})


def fr_indi_065() -> None:
    """FR-INDI-065: Demonstrate momentum acceleration."""
    run_requirement(
        "FR-INDI-065", "momentum_acceleration", {"k": 2, "unit_seconds": 300.0}
    )


def fr_indi_066() -> None:
    """FR-INDI-066: Demonstrate volume acceleration."""
    run_requirement(
        "FR-INDI-066",
        "volume_acceleration",
        {"window": 3, "k": 2, "unit_seconds": 300.0},
    )


def fr_indi_067() -> None:
    """FR-INDI-067: Demonstrate the declared bar-arrival-rate proxy."""
    run_requirement(
        "FR-INDI-067", "market_event_arrival_rate", {"window_seconds": 900.0}
    )


def fr_indi_068() -> None:
    """FR-INDI-068: Demonstrate volatility expansion rate."""
    run_requirement(
        "FR-INDI-068",
        "volatility_expansion_rate",
        {"atr_period": 3, "k": 2, "unit_seconds": 300.0},
    )


def fr_indi_069() -> None:
    """FR-INDI-069: Demonstrate the composite market-speed gauge."""
    run_requirement(
        "FR-INDI-069",
        "composite_market_speed_gauge",
        {
            "k": 2,
            "unit_seconds": 300.0,
            "volume_window": 3,
            "atr_period": 3,
            "z_window": 3,
            "z_max": 3.0,
            "weight_price_velocity": 0.25,
            "weight_momentum_acceleration": 0.25,
            "weight_volume_acceleration": 0.25,
            "weight_volatility_expansion": 0.25,
        },
    )


def main() -> None:
    """Exercise every Market Speed public operation."""
    fr_indi_064()
    fr_indi_065()
    fr_indi_066()
    fr_indi_067()
    fr_indi_068()
    fr_indi_069()


if __name__ == "__main__":
    main()
