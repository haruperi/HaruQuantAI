"""Standalone Manual-Plan Support feature evidence."""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import build_manual_trade_plan, validate_manual_trade_plan


def _emit(requirement: str, value: object) -> None:
    """Print one success message and genuine produced value."""
    print(f"Success: {requirement}")
    print(value)


def _plan() -> dict[str, object]:
    return build_manual_trade_plan(
        player_ref="ply-1",
        strategy_id="trend",
        strategy_version="1.0.0",
        symbol="EURUSD",
        direction="BUY",
        entry_rule="closed-bar breakout",
        entry_price=Decimal("1.10"),
        invalidation_rule="close below support",
        stop_price=Decimal("1.09"),
        target_price=Decimal("1.12"),
        exit_plan_ref="exit-1",
        operating_envelope_ref="env-1",
        requested_size_basis="risk-budget",
        planned_rationale="verified setup",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def fr_str_060() -> None:
    _emit("FR-STR-060", _plan())


def fr_str_061() -> None:
    _emit("FR-STR-061", validate_manual_trade_plan(_plan()))


def fr_str_062() -> None:
    _emit("FR-STR-062", validate_manual_trade_plan(_plan())["author_ref"])


def main() -> None:
    """Run every Manual-Plan Support requirement example."""
    fr_str_060()
    fr_str_061()
    fr_str_062()


if __name__ == "__main__":
    main()
