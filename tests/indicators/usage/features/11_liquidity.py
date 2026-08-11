"""Standalone usage evidence for FEAT-INDI-11."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.indicators.usage._migration_support import run_requirement


def fr_indi_076() -> None:
    """FR-INDI-076: Demonstrate Amihud illiquidity."""
    run_requirement("FR-INDI-076", "amihud_illiquidity", {"window": 3})


def main() -> None:
    """Exercise the OHLCV-calculable Liquidity operation."""
    fr_indi_076()


if __name__ == "__main__":
    main()
