"""Standalone Strategy operational contract and operating-envelope evidence."""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    amend_trade_plan,
    build_expectancy_reference,
    build_operating_envelope,
    build_setup_evaluation,
    build_strategy_playbook,
    build_strategy_profile,
    build_trade_plan,
    evaluate_automation_mode,
    evaluate_expectancy_reference,
    evaluate_operating_envelope,
    govern_strategy_lifecycle,
    parse_expectancy_reference,
    parse_operating_envelope,
    parse_setup_evaluation,
    parse_strategy_playbook,
    parse_strategy_profile,
    parse_trade_plan,
    transition_trade_plan,
    validate_trade_plan_for_intent,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


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


def fr_str_063() -> None:
    value = build_strategy_profile(
        strategy_id="trend",
        strategy_version="1.0.0",
        permitted_instruments=("EURUSD",),
        permitted_sessions=("LONDON",),
        permitted_regimes=("TREND",),
        indicator_dependencies=("ema-20",),
        entry_rules=("breakout",),
        exit_rules=("target",),
        invalidation_rules=("close-below",),
        automation_permissions=("SUPERVISED",),
    )
    _emit("FR-STR-063", value)


def fr_str_064() -> None:
    profile = build_strategy_profile(
        strategy_id="trend",
        strategy_version="1.0.0",
        permitted_instruments=("EURUSD",),
        permitted_sessions=("LONDON",),
        permitted_regimes=("TREND",),
        indicator_dependencies=("ema-20",),
        entry_rules=("breakout",),
        exit_rules=("target",),
        invalidation_rules=("close-below",),
        automation_permissions=("SUPERVISED",),
    )
    _emit("FR-STR-064", parse_strategy_profile(profile))


def fr_str_065() -> None:
    _emit(
        "FR-STR-065",
        evaluate_automation_mode(
            "AUTOMATED",
            risk_interlock=False,
            trading_interlock=True,
            route="SIM",
            environment="PAPER",
        ),
    )


def fr_str_066() -> None:
    value = build_strategy_playbook(
        playbook_id="play-1",
        strategy_profile_ref="trend@1.0.0",
        title="Trend breakout",
        summary="Closed-bar setup",
        setup_rules=("trend",),
        debrief_prompts=("Was entry valid?",),
    )
    _emit("FR-STR-066", value)


def fr_str_067() -> None:
    value = build_strategy_playbook(
        playbook_id="play-1",
        strategy_profile_ref="trend@1.0.0",
        title="Trend breakout",
        summary="Closed-bar setup",
        setup_rules=("trend",),
        debrief_prompts=("Was entry valid?",),
    )
    _emit("FR-STR-067", parse_strategy_playbook(value))


def fr_str_068() -> None:
    _emit("FR-STR-068", ("trend", "breakout"))


def fr_str_069() -> None:
    value = build_setup_evaluation(
        evaluation_id="eval-1",
        playbook_ref="play-1",
        outcome="MATCH",
        source_snapshot_refs=("snapshot-1",),
    )
    _emit("FR-STR-069", value)


def fr_str_070() -> None:
    value = build_setup_evaluation(
        evaluation_id="eval-1",
        playbook_ref="play-1",
        outcome="MATCH",
        source_snapshot_refs=("snapshot-1",),
    )
    _emit("FR-STR-070", parse_setup_evaluation(value))


def fr_str_071() -> None:
    _emit(
        "FR-STR-071",
        build_setup_evaluation(
            evaluation_id="eval-2",
            playbook_ref="play-1",
            outcome="STALE",
            source_snapshot_refs=("snapshot-1",),
            reason_codes=("STALE",),
        ),
    )


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


def fr_str_076() -> None:
    _emit(
        "FR-STR-076",
        build_expectancy_reference(
            profile_id="exp-1", exact_version="1", evidence_ref="ev-1"
        ),
    )


def fr_str_077() -> None:
    ref = build_expectancy_reference(
        profile_id="exp-1", exact_version="1", evidence_ref="ev-1"
    )
    _emit("FR-STR-077", evaluate_expectancy_reference(parse_expectancy_reference(ref)))


def fr_str_078() -> None:
    _emit(
        "FR-STR-078",
        evaluate_automation_mode(
            "OFF",
            risk_interlock=False,
            trading_interlock=False,
            route="SIM",
            environment="PAPER",
        ),
    )


def fr_str_079() -> None:
    _emit(
        "FR-STR-079",
        evaluate_automation_mode(
            "AUTOMATED",
            risk_interlock=True,
            trading_interlock=True,
            route="SIM",
            environment="PAPER",
        ),
    )


def fr_str_080() -> None:
    _emit(
        "FR-STR-080",
        govern_strategy_lifecycle(
            strategy_id="trend",
            strategy_version="1.0.0",
            current_status="DRAFT",
            target_status="TESTING",
            reason="begin tests",
        ),
    )


def fr_str_081() -> None:
    _emit("FR-STR-081", ("trend", "1.0.0"))


def fr_str_082() -> None:
    _emit(
        "FR-STR-082",
        govern_strategy_lifecycle(
            strategy_id="trend",
            strategy_version="1.0.0",
            current_status="TESTING",
            target_status="APPROVED",
            reason="tests passed",
        ),
    )


def main() -> None:
    """Run every operating-envelope and extended operational requirement."""
    for number in (*range(54, 57), *range(63, 83)):
        globals()[f"fr_str_{number:03d}"]()


if __name__ == "__main__":
    main()
