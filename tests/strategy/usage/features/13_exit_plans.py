"""Standalone ExitPlan feature evidence."""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    build_exit_plan,
    build_exit_plan_handoff,
    parse_exit_plan,
)


def _emit(requirement: str, value: object) -> None:
    """Print one success message and genuine produced value."""
    print(f"Success: {requirement}")
    print(value)


def _plan() -> dict[str, object]:
    return build_exit_plan(
        exit_plan_id="exit-1",
        initial_stop=Decimal("1.09"),
        target=Decimal("1.12"),
        partial_exit_fractions=(Decimal("0.5"),),
        trailing_rule="atr",
        time_stop_seconds=3600,
        invalidation_rule="close below support",
        automation_handoff="SUPERVISED",
    )


def fr_str_057() -> None:
    _emit("FR-STR-057", _plan())


def fr_str_058() -> None:
    _emit("FR-STR-058", parse_exit_plan(_plan()))


def fr_str_059() -> None:
    _emit(
        "FR-STR-059",
        build_exit_plan_handoff(
            _plan(),
            risk_interlock=True,
            trading_interlock=True,
            route="SIM",
            environment="PAPER",
        ),
    )


def main() -> None:
    """Run every ExitPlan requirement example."""
    fr_str_057()
    fr_str_058()
    fr_str_059()


if __name__ == "__main__":
    main()
