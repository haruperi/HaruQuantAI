"""Unit evidence for Strategy application contracts."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.strategy import (
    amend_trade_plan,
    build_exit_plan,
    build_exit_plan_handoff,
    build_expectancy_reference,
    build_manual_trade_plan,
    build_operating_envelope,
    build_setup_evaluation,
    build_strategy_playbook,
    build_strategy_profile,
    build_trade_plan,
    evaluate_automation_mode,
    evaluate_expectancy_reference,
    evaluate_operating_envelope,
    govern_strategy_lifecycle,
    parse_exit_plan,
    parse_expectancy_reference,
    parse_operating_envelope,
    parse_setup_evaluation,
    parse_strategy_playbook,
    parse_strategy_profile,
    parse_trade_plan,
    transition_trade_plan,
    validate_manual_trade_plan,
    validate_trade_plan_for_intent,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _plan(*, author_type: str = "STRATEGY") -> dict[str, object]:
    """Build one deterministic plan fixture."""
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
        author_type=author_type,
        created_at=NOW,
    )


def test_profile_playbook_and_setup_round_trip() -> None:
    """Verify strict profile, playbook, and setup transports."""
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
    assert parse_strategy_profile(profile) == profile
    playbook = build_strategy_playbook(
        playbook_id="play-1",
        strategy_profile_ref="trend@1.0.0",
        title="Trend breakout",
        summary="Closed-bar breakout setup",
        setup_rules=("trend", "breakout"),
        debrief_prompts=("Was entry valid?",),
    )
    assert parse_strategy_playbook(playbook) == playbook
    evaluation = build_setup_evaluation(
        evaluation_id="eval-1",
        playbook_ref="play-1",
        outcome="MATCH",
        source_snapshot_refs=("snapshot-1",),
    )
    assert parse_setup_evaluation(evaluation) == evaluation


def test_trade_plan_lifecycle_is_immutable_and_sim_only() -> None:
    """Verify lifecycle transitions, amendments, and operational route discipline."""
    draft = _plan()
    ready = transition_trade_plan(draft, target_status="READY_FOR_RISK")
    assert draft["status"] == "DRAFT"
    assert ready["status"] == "READY_FOR_RISK"
    assert (
        validate_trade_plan_for_intent(ready, route="SIM", environment="PAPER") == ready
    )
    with pytest.raises(ValueError, match="simulation-only"):
        validate_trade_plan_for_intent(ready, route="LIVE", environment="LIVE")
    approved = transition_trade_plan(ready, target_status="APPROVED")
    released = transition_trade_plan(approved, target_status="RELEASED")
    amended = amend_trade_plan(released, created_at=NOW, target_price=Decimal("1.13"))
    assert amended["parent_plan_id"] == released["plan_id"]
    assert amended["plan_version"] == 2
    assert parse_trade_plan(amended) == amended


def test_operating_exit_manual_expectancy_and_governance_fail_closed() -> None:
    """Verify remaining operational policies and fail-closed fallbacks."""
    envelope = build_operating_envelope(
        envelope_id="env-1",
        max_volatility=Decimal(2),
        max_spread=Decimal("0.1"),
        min_liquidity=Decimal(10),
        permitted_regimes=("TREND",),
        permitted_sessions=("LONDON",),
        max_holding_seconds=3600,
        blocked_event_types=("NEWS",),
    )
    assert parse_operating_envelope(envelope) == envelope
    assert (
        evaluate_operating_envelope(
            envelope,
            volatility=None,
            spread=Decimal("0.01"),
            liquidity=Decimal(20),
            regime="TREND",
            session="LONDON",
            active_event_types=(),
        )
        == "RESTRICTED"
    )
    assert (
        evaluate_operating_envelope(
            envelope,
            volatility=Decimal(1),
            spread=Decimal("0.01"),
            liquidity=Decimal(20),
            regime="TREND",
            session="LONDON",
            active_event_types=(),
        )
        == "PERMITTED"
    )
    assert (
        evaluate_operating_envelope(
            envelope,
            volatility=Decimal(3),
            spread=Decimal("0.01"),
            liquidity=Decimal(20),
            regime="TREND",
            session="LONDON",
            active_event_types=(),
        )
        == "RESTRICTED"
    )
    exit_plan = build_exit_plan(
        exit_plan_id="exit-1",
        initial_stop=Decimal("1.09"),
        target=Decimal("1.12"),
        partial_exit_fractions=(Decimal("0.5"),),
        trailing_rule="atr",
        time_stop_seconds=3600,
        invalidation_rule="close below support",
        automation_handoff="SUPERVISED",
    )
    assert parse_exit_plan(exit_plan) == exit_plan
    assert (
        build_exit_plan_handoff(
            exit_plan,
            risk_interlock=True,
            trading_interlock=True,
            route="SIM",
            environment="PAPER",
        )["status"]
        == "READY"
    )
    reference = build_expectancy_reference(
        profile_id="expectancy-1", exact_version="1", evidence_ref="evidence-1"
    )
    assert parse_expectancy_reference(reference) == reference
    assert evaluate_expectancy_reference(reference) == "NOT_ELIGIBLE"
    assert (
        evaluate_expectancy_reference(
            reference,
            provider=lambda value: {
                "status": "ELIGIBLE",
                "profile_id": value["profile_id"],
                "exact_version": value["exact_version"],
            },
        )
        == "ELIGIBLE"
    )
    assert (
        evaluate_expectancy_reference(
            reference,
            provider=lambda _value: (_ for _ in ()).throw(RuntimeError("offline")),
        )
        == "NOT_ELIGIBLE"
    )
    assert (
        evaluate_automation_mode(
            "AUTOMATED",
            risk_interlock=False,
            trading_interlock=True,
            route="SIM",
            environment="PAPER",
        )
        == "RESTRICTED"
    )
    assert (
        evaluate_automation_mode(
            "OFF",
            risk_interlock=False,
            trading_interlock=False,
            route="SIM",
            environment="PAPER",
        )
        == "OFF"
    )
    assert (
        evaluate_automation_mode(
            "SUPERVISED",
            risk_interlock=True,
            trading_interlock=True,
            route="SIM",
            environment="PAPER",
        )
        == "SUPERVISED"
    )
    with pytest.raises(ValueError, match="unknown automation"):
        evaluate_automation_mode(
            "UNKNOWN",
            risk_interlock=True,
            trading_interlock=True,
            route="SIM",
            environment="PAPER",
        )
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
    assert validate_manual_trade_plan(manual)["author_ref"] == "ply-1"
    mutation = govern_strategy_lifecycle(
        strategy_id="trend",
        strategy_version="1.0.0",
        current_status="TESTING",
        target_status="APPROVED",
        reason="tests passed",
    )
    assert mutation["to_status"] == "APPROVED"
    with pytest.raises(ValueError, match="transition"):
        govern_strategy_lifecycle(
            strategy_id="trend",
            strategy_version="1.0.0",
            current_status="RETIRED",
            target_status="APPROVED",
            reason="invalid",
        )
    with pytest.raises(ValueError, match="non-empty"):
        govern_strategy_lifecycle(
            strategy_id="",
            strategy_version="1.0.0",
            current_status="TESTING",
            target_status="APPROVED",
            reason="invalid",
        )


def test_operational_contracts_reject_invalid_relationships() -> None:
    """Cover strict validation branches for operational contracts."""
    with pytest.raises(ValueError, match="non-empty"):
        build_expectancy_reference(profile_id="", exact_version="1", evidence_ref="e")
    with pytest.raises(ValueError, match="partial exits"):
        build_exit_plan(
            exit_plan_id="exit",
            initial_stop=Decimal(1),
            target=Decimal(2),
            partial_exit_fractions=(Decimal("0.8"), Decimal("0.7")),
            trailing_rule=None,
            time_stop_seconds=None,
            invalidation_rule="rule",
            automation_handoff="NONE",
        )
    with pytest.raises(ValueError, match="thresholds"):
        build_operating_envelope(
            envelope_id="env",
            max_volatility=Decimal(-1),
            max_spread=Decimal(1),
            min_liquidity=Decimal(1),
            permitted_regimes=("TREND",),
            permitted_sessions=("LONDON",),
            max_holding_seconds=1,
            blocked_event_types=(),
        )


def test_setup_evaluation_rejects_invalid_shapes() -> None:
    """Cover strict setup-evaluation validation branches."""
    with pytest.raises(ValueError, match="identity must be non-empty"):
        build_setup_evaluation(
            evaluation_id="",
            playbook_ref="play-1",
            outcome="MATCH",
            source_snapshot_refs=("snapshot-1",),
        )
    with pytest.raises(ValueError, match="requires source snapshots"):
        build_setup_evaluation(
            evaluation_id="eval-1",
            playbook_ref="play-1",
            outcome="MATCH",
            source_snapshot_refs=(),
        )
    with pytest.raises(ValueError, match="cannot carry failure reasons"):
        build_setup_evaluation(
            evaluation_id="eval-1",
            playbook_ref="play-1",
            outcome="MATCH",
            source_snapshot_refs=("snapshot-1",),
            reason_codes=("STALE",),
        )
    with pytest.raises(ValueError, match="require reason codes"):
        build_setup_evaluation(
            evaluation_id="eval-1",
            playbook_ref="play-1",
            outcome="STALE",
            source_snapshot_refs=("snapshot-1",),
        )
