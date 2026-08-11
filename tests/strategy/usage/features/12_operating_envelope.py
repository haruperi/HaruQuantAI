"""Standalone Operating Envelope feature evidence."""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    build_operating_envelope,
    evaluate_operating_envelope,
    parse_operating_envelope,
)


def _emit(requirement: str, value: object) -> None:
    """Print exactly one success message and its genuine produced value."""
    print(f"Success: {requirement}")
    print(value)


def _envelope() -> dict[str, object]:
    return build_operating_envelope(
        envelope_id="env-1",
        max_volatility=Decimal(2),
        max_spread=Decimal("0.1"),
        min_liquidity=Decimal(10),
        permitted_regimes=("TREND",),
        permitted_sessions=("LONDON",),
        max_holding_seconds=3600,
        blocked_event_types=("NEWS",),
    )


def fr_str_054() -> None:
    _emit("FR-STR-054", _envelope())


def fr_str_055() -> None:
    _emit("FR-STR-055", parse_operating_envelope(_envelope()))


def fr_str_056() -> None:
    _emit(
        "FR-STR-056",
        evaluate_operating_envelope(
            _envelope(),
            volatility=Decimal(1),
            spread=Decimal("0.01"),
            liquidity=Decimal(20),
            regime="TREND",
            session="LONDON",
            active_event_types=(),
        ),
    )


def main() -> None:
    """Run every Operating Envelope requirement example."""
    for number in range(54, 57):
        globals()[f"fr_str_{number:03d}"]()


if __name__ == "__main__":
    main()
