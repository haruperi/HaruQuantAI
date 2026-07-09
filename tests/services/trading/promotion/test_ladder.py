"""Unit tests for the promotion ladder validation module."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.trading.contracts import (
    MutationCapability,
    PromotionStage,
    QuoteSnapshot,
    TradingAction,
    TradingRequestEnvelope,
    TradingRoute,
)
from app.services.trading.gates._common import GateStepStatus
from app.services.trading.gates.approval import ApprovalScope, OperatorApprovalToken
from app.services.trading.promotion.ladder import (
    compute_canonical_promotion_hash,
    evaluate_promotion_stage_gate,
    validate_promotion_transition,
    validate_route_stage_capability,
)
from app.services.trading.security.error_mapping import (
    TradingMappedError,
    TradingValidationError,
)


class MockClock:
    """Mock clock for deterministic tests."""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def now_utc(self) -> datetime:
        return self._now

    def now_ptp(self) -> datetime:
        return self._now

    def monotonic(self) -> float:
        return 0.0


def make_approval_token(
    *,
    approval_id: str = "app-1",
    operator_id: str = "op-1",
    governed_action_id: str = "promote_to_simulation",
    strategy_id: str = "strat-1",
    request_hash: str,
    expires_in_secs: int = 60,
    revoked: bool = False,
    consumed: bool = False,
    now: datetime,
) -> OperatorApprovalToken:
    """Helper to build a valid OperatorApprovalToken."""
    return OperatorApprovalToken(
        approval_id=approval_id,
        operator_id=operator_id,
        governed_action_id=governed_action_id,
        scope=ApprovalScope(strategy_id=strategy_id),
        canonical_request_hash=request_hash,
        issued_at=(now - timedelta(seconds=10)).isoformat(),
        expires_at=(now + timedelta(seconds=expires_in_secs)).isoformat(),
        revoked=revoked,
        consumed=consumed,
    )


def test_validate_route_stage_capability_valid_combinations() -> None:
    """Test that all defined route matrix combinations pass validation."""
    # SIM route
    validate_route_stage_capability(
        TradingRoute.SIM, PromotionStage.OFFLINE_TEST, MutationCapability.READ_ONLY
    )
    validate_route_stage_capability(
        TradingRoute.SIM,
        PromotionStage.SIMULATION,
        MutationCapability.PACKAGED_ONLY,
    )

    # PAPER route
    validate_route_stage_capability(
        TradingRoute.PAPER,
        PromotionStage.PAPER_TRADING,
        MutationCapability.PAPER_ONLY,
    )

    # SHADOW route
    validate_route_stage_capability(
        TradingRoute.SHADOW,
        PromotionStage.SHADOW_TRADING,
        MutationCapability.SHADOW_ONLY,
    )

    # LIVE route
    validate_route_stage_capability(
        TradingRoute.LIVE,
        PromotionStage.READ_ONLY_BROKER_CONNECTION,
        MutationCapability.READ_ONLY,
    )
    validate_route_stage_capability(
        TradingRoute.LIVE, PromotionStage.MICRO_LIVE, MutationCapability.MICRO_LIVE
    )
    validate_route_stage_capability(
        TradingRoute.LIVE, PromotionStage.FULL_LIVE, MutationCapability.FULL_LIVE
    )


def test_validate_route_stage_capability_invalid_combinations() -> None:
    """Test that invalid combinations raise validation errors."""
    with pytest.raises(TradingValidationError, match="not allowed for route"):
        validate_route_stage_capability(
            TradingRoute.SIM,
            PromotionStage.FULL_LIVE,
            MutationCapability.FULL_LIVE,
        )

    with pytest.raises(TradingValidationError, match="not allowed for route"):
        validate_route_stage_capability(
            TradingRoute.PAPER,
            PromotionStage.OFFLINE_TEST,
            MutationCapability.PACKAGED_ONLY,
        )

    with pytest.raises(TradingValidationError, match="not allowed for route"):
        validate_route_stage_capability(
            TradingRoute.LIVE,
            PromotionStage.PAPER_TRADING,
            MutationCapability.PAPER_ONLY,
        )

    with pytest.raises(TradingValidationError, match="is not allowed for route"):
        validate_route_stage_capability(
            TradingRoute.LIVE,
            PromotionStage.MICRO_LIVE,
            MutationCapability.FULL_LIVE,
        )

    match_msg = "not configured in the capability matrix"
    with pytest.raises(TradingValidationError, match=match_msg):
        validate_route_stage_capability(
            "invalid_route",  # type: ignore[arg-type]
            PromotionStage.FULL_LIVE,
            MutationCapability.FULL_LIVE,
        )


def test_evaluate_promotion_stage_gate_passes() -> None:
    """Test that evaluate_promotion_stage_gate accepts valid requests."""
    request = TradingRequestEnvelope(
        route=TradingRoute.LIVE,
        action=TradingAction.SUBMIT_ORDER,
        promotion_stage=PromotionStage.MICRO_LIVE,
        mutation_capability=MutationCapability.MICRO_LIVE,
        request_id="req-1",
        correlation_id="corr-1",
        symbol="EURUSD",
        quote_snapshot=QuoteSnapshot(
            symbol="EURUSD",
            bid=Decimal("1.1000"),
            ask=Decimal("1.1002"),
            spread=Decimal("0.0002"),
            timestamp="2026-07-09T10:00:00Z",
            source="test",
            freshness_age_ms=10,
        ),
    )
    result = evaluate_promotion_stage_gate(request=request)
    assert result.status is GateStepStatus.PASSED


def test_evaluate_promotion_stage_gate_blocks() -> None:
    """Test that evaluate_promotion_stage_gate blocks invalid requests."""
    request = TradingRequestEnvelope(
        route=TradingRoute.SIM,
        action=TradingAction.SUBMIT_ORDER,
        promotion_stage=PromotionStage.FULL_LIVE,  # Invalid for SIM
        mutation_capability=MutationCapability.FULL_LIVE,
        request_id="req-1",
        correlation_id="corr-1",
        symbol="EURUSD",
    )
    result = evaluate_promotion_stage_gate(request=request)
    assert result.status is GateStepStatus.BLOCKED
    assert result.reason_code == "VALIDATION_FAILED"


def test_validate_promotion_transition_invalid_stages() -> None:
    """Test that invalid stage values raise validation errors."""
    clock = MockClock(datetime(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(TradingValidationError, match="Invalid current stage"):
        validate_promotion_transition(
            strategy_id="strat-1",
            current_stage="invalid_stage",  # type: ignore[arg-type]
            target_stage=PromotionStage.SIMULATION,
            approvals=(),
            clock=clock,
            risk_policy_ok=True,
            reconciliation_state_ok=True,
            audit_sinks_ok=True,
        )
    with pytest.raises(TradingValidationError, match="Invalid target stage"):
        validate_promotion_transition(
            strategy_id="strat-1",
            current_stage=PromotionStage.OFFLINE_TEST,
            target_stage="invalid_stage",  # type: ignore[arg-type]
            approvals=(),
            clock=clock,
            risk_policy_ok=True,
            reconciliation_state_ok=True,
            audit_sinks_ok=True,
        )


def test_validate_promotion_transition_noop_and_demotion() -> None:
    """Test that no-ops and demotions pass without approvals or prerequisites."""
    clock = MockClock(datetime(2026, 7, 9, 12, 0, tzinfo=UTC))

    # No-op: target == current
    validate_promotion_transition(
        strategy_id="strat-1",
        current_stage=PromotionStage.SIMULATION,
        target_stage=PromotionStage.SIMULATION,
        approvals=(),
        clock=clock,
        risk_policy_ok=False,
        reconciliation_state_ok=False,
        audit_sinks_ok=False,
    )

    # Demotion: target < current
    validate_promotion_transition(
        strategy_id="strat-1",
        current_stage=PromotionStage.FULL_LIVE,
        target_stage=PromotionStage.READ_ONLY_BROKER_CONNECTION,
        approvals=(),
        clock=clock,
        risk_policy_ok=False,
        reconciliation_state_ok=False,
        audit_sinks_ok=False,
    )


def test_validate_promotion_transition_skips_steps_fails() -> None:
    """Test that skipping steps forward is blocked."""
    clock = MockClock(datetime(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(TradingValidationError, match="cannot skip steps"):
        validate_promotion_transition(
            strategy_id="strat-1",
            current_stage=PromotionStage.OFFLINE_TEST,
            target_stage=PromotionStage.REPLAY,  # Skips SIMULATION
            approvals=(),
            clock=clock,
            risk_policy_ok=True,
            reconciliation_state_ok=True,
            audit_sinks_ok=True,
        )


def test_validate_promotion_transition_self_promotion_fails() -> None:
    """Test that self-promotion without approvals is blocked."""
    clock = MockClock(datetime(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(TradingValidationError, match="cannot self-promote"):
        validate_promotion_transition(
            strategy_id="strat-1",
            current_stage=PromotionStage.OFFLINE_TEST,
            target_stage=PromotionStage.SIMULATION,
            approvals=(),
            clock=clock,
            risk_policy_ok=True,
            reconciliation_state_ok=True,
            audit_sinks_ok=True,
        )


def test_validate_promotion_transition_prerequisites_fails() -> None:
    """Test that failing prerequisites blocks the transition."""
    clock = MockClock(datetime(2026, 7, 9, 12, 0, tzinfo=UTC))
    now = clock.now_utc()
    r_hash = compute_canonical_promotion_hash(
        strategy_id="strat-1",
        current_stage=PromotionStage.OFFLINE_TEST,
        target_stage=PromotionStage.SIMULATION,
    )
    token = make_approval_token(
        governed_action_id="promote_to_simulation",
        request_hash=r_hash,
        now=now,
    )

    # Risk policy unhealthy
    with pytest.raises(TradingValidationError, match="Risk policy prerequisites"):
        validate_promotion_transition(
            strategy_id="strat-1",
            current_stage=PromotionStage.OFFLINE_TEST,
            target_stage=PromotionStage.SIMULATION,
            approvals=(token,),
            clock=clock,
            risk_policy_ok=False,
            reconciliation_state_ok=True,
            audit_sinks_ok=True,
        )

    # Reconciliation state unresolved
    with pytest.raises(TradingValidationError, match="Reconciliation state"):
        validate_promotion_transition(
            strategy_id="strat-1",
            current_stage=PromotionStage.OFFLINE_TEST,
            target_stage=PromotionStage.SIMULATION,
            approvals=(token,),
            clock=clock,
            risk_policy_ok=True,
            reconciliation_state_ok=False,
            audit_sinks_ok=True,
        )

    # Audit sinks unhealthy
    with pytest.raises(TradingValidationError, match="Audit sinks"):
        validate_promotion_transition(
            strategy_id="strat-1",
            current_stage=PromotionStage.OFFLINE_TEST,
            target_stage=PromotionStage.SIMULATION,
            approvals=(token,),
            clock=clock,
            risk_policy_ok=True,
            reconciliation_state_ok=True,
            audit_sinks_ok=False,
        )


def test_validate_promotion_transition_mismatched_action_fails() -> None:
    """Test that mismatched approval action ID blocks transition."""
    clock = MockClock(datetime(2026, 7, 9, 12, 0, tzinfo=UTC))
    now = clock.now_utc()
    token = make_approval_token(
        governed_action_id="promote_to_replay",  # Wrong action
        request_hash="wronghash",
        now=now,
    )
    with pytest.raises(TradingValidationError, match="Mismatched approval token"):
        validate_promotion_transition(
            strategy_id="strat-1",
            current_stage=PromotionStage.OFFLINE_TEST,
            target_stage=PromotionStage.SIMULATION,
            approvals=(token,),
            clock=clock,
            risk_policy_ok=True,
            reconciliation_state_ok=True,
            audit_sinks_ok=True,
        )


def test_validate_promotion_transition_single_operator_success() -> None:
    """Test single operator approval promotion validation path."""
    clock = MockClock(datetime(2026, 7, 9, 12, 0, tzinfo=UTC))
    now = clock.now_utc()
    r_hash = compute_canonical_promotion_hash(
        strategy_id="strat-1",
        current_stage=PromotionStage.OFFLINE_TEST,
        target_stage=PromotionStage.SIMULATION,
    )
    token = make_approval_token(
        governed_action_id="promote_to_simulation",
        request_hash=r_hash,
        now=now,
    )

    # Should succeed without throwing
    validate_promotion_transition(
        strategy_id="strat-1",
        current_stage=PromotionStage.OFFLINE_TEST,
        target_stage=PromotionStage.SIMULATION,
        approvals=(token,),
        clock=clock,
        risk_policy_ok=True,
        reconciliation_state_ok=True,
        audit_sinks_ok=True,
    )


def test_validate_promotion_transition_dual_operator_success() -> None:
    """Test that full_live requires and accepts valid dual operator approval."""
    clock = MockClock(datetime(2026, 7, 9, 12, 0, tzinfo=UTC))
    now = clock.now_utc()
    r_hash = compute_canonical_promotion_hash(
        strategy_id="strat-1",
        current_stage=PromotionStage.MICRO_LIVE,
        target_stage=PromotionStage.FULL_LIVE,
    )

    # 1. Only one token presented -> fail
    token1 = make_approval_token(
        approval_id="app-1",
        operator_id="op-1",
        governed_action_id="promote_to_full_live",
        request_hash=r_hash,
        now=now,
    )
    match_msg1 = "Dual-operator approval requires two distinct operator tokens"
    with pytest.raises(TradingMappedError, match=match_msg1):
        validate_promotion_transition(
            strategy_id="strat-1",
            current_stage=PromotionStage.MICRO_LIVE,
            target_stage=PromotionStage.FULL_LIVE,
            approvals=(token1,),
            clock=clock,
            risk_policy_ok=True,
            reconciliation_state_ok=True,
            audit_sinks_ok=True,
        )

    # 2. Mismatched operators (same operator ID on both tokens) -> fail
    token2 = make_approval_token(
        approval_id="app-2",
        operator_id="op-1",  # Same operator
        governed_action_id="promote_to_full_live",
        request_hash=r_hash,
        now=now,
    )
    match_msg2 = "Dual-operator approval requires two distinct operators"
    with pytest.raises(TradingMappedError, match=match_msg2):
        validate_promotion_transition(
            strategy_id="strat-1",
            current_stage=PromotionStage.MICRO_LIVE,
            target_stage=PromotionStage.FULL_LIVE,
            approvals=(token1, token2),
            clock=clock,
            risk_policy_ok=True,
            reconciliation_state_ok=True,
            audit_sinks_ok=True,
        )

    # 3. Two distinct valid operators -> succeed
    token3 = make_approval_token(
        approval_id="app-3",
        operator_id="op-2",  # Distinct operator
        governed_action_id="promote_to_full_live",
        request_hash=r_hash,
        now=now,
    )
    validate_promotion_transition(
        strategy_id="strat-1",
        current_stage=PromotionStage.MICRO_LIVE,
        target_stage=PromotionStage.FULL_LIVE,
        approvals=(token1, token3),
        clock=clock,
        risk_policy_ok=True,
        reconciliation_state_ok=True,
        audit_sinks_ok=True,
    )
