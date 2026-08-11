"""Standalone Canonical Trade Plans and Lifecycle feature evidence."""

import os
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    amend_trade_plan,
    build_manual_trade_plan,
    build_trade_plan,
    ensure_strategy_storage,
    list_trade_plans,
    parse_trade_plan,
    persist_trade_plan,
    transition_trade_plan,
    validate_manual_trade_plan,
    validate_trade_plan_for_intent,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)
_REQUEST = "req-00000000-0000-4000-8000-000000000099"
_CORRELATION = "cor-00000000-0000-4000-8000-000000000099"


def _emit(requirement: str, value: object) -> None:
    """Print exactly one success message and its genuine produced value."""
    print(f"Success: {requirement}")
    print(value)


def _plan() -> dict[str, object]:
    return build_trade_plan(
        plan_version=1,
        status="DRAFT",
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
        author_type="STRATEGY",
        created_at=NOW,
    )


def _persist_demonstration() -> None:
    """Exercise production trade-plan persistence and listing when enabled."""
    if os.environ.get("RUN_STRATEGY_STATEFUL_USAGE") != "1":
        return
    ensure_strategy_storage(_REQUEST)
    persisted = persist_trade_plan(
        _plan(), request_id=_REQUEST, correlation_id=_CORRELATION
    )
    _emit("FEAT-STR-16 persistence", persisted["record_hash"])
    _emit(
        "FEAT-STR-16 trade plan list",
        list_trade_plans(request_id=_REQUEST, plan_id=_plan()["plan_id"]),
    )


def fr_str_060() -> None:
    _emit(
        "FR-STR-060",
        build_manual_trade_plan(
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
            created_at=NOW,
        ),
    )


def fr_str_061() -> None:
    manual = build_manual_trade_plan(
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
        created_at=NOW,
    )
    _emit("FR-STR-061", validate_manual_trade_plan(manual))


def fr_str_062() -> None:
    manual = build_manual_trade_plan(
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
        created_at=NOW,
    )
    _emit("FR-STR-062", validate_manual_trade_plan(manual)["author_ref"])


def fr_str_072() -> None:
    _emit("FR-STR-072", _plan())


def fr_str_073() -> None:
    _emit("FR-STR-073", parse_trade_plan(_plan()))


def fr_str_074() -> None:
    ready = transition_trade_plan(_plan(), target_status="READY_FOR_RISK")
    _emit(
        "FR-STR-074",
        validate_trade_plan_for_intent(ready, route="SIM", environment="PAPER"),
    )


def fr_str_075() -> None:
    ready = transition_trade_plan(_plan(), target_status="READY_FOR_RISK")
    approved = transition_trade_plan(ready, target_status="APPROVED")
    released = transition_trade_plan(approved, target_status="RELEASED")
    _emit(
        "FR-STR-075",
        amend_trade_plan(released, created_at=NOW, target_price=Decimal("1.13")),
    )


def main() -> None:
    """Run every Canonical Trade Plans and Lifecycle requirement example."""
    for number in (*range(60, 63), *range(72, 76)):
        globals()[f"fr_str_{number:03d}"]()
    _persist_demonstration()


if __name__ == "__main__":
    main()
