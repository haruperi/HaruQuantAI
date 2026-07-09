"""Promotion ladder stages and transition validation logic.

This module enforces the route-capability compatibility matrix (TRD-FR-182),
verifies operator approvals for stage transitions (TRD-FR-183), checks all
prerequisites to prevent self-promotion (TRD-FR-184), and exposes the
Gate 3 pipeline evaluator.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from app.services.trading.contracts import (
    MutationCapability,
    PromotionStage,
    TradingRoute,
)
from app.services.trading.gates._common import (
    GateName,
    GateStepResult,
    blocked_step,
    passed_step,
)
from app.services.trading.gates.approval import (
    ApprovalScope,
    validate_dual_operator_approval,
    validate_operator_approval,
)
from app.services.trading.security.error_mapping import TradingValidationError
from app.utils.logger import logger
from app.utils.standard import canonical_json

if TYPE_CHECKING:
    from app.services.trading.contracts import TradingRequestEnvelope
    from app.services.trading.gates.approval import OperatorApprovalToken
    from app.services.trading.state.ports import Clock

# Strict linear promotion sequence mapping
PROMOTION_SEQUENCE = [
    PromotionStage.OFFLINE_TEST,
    PromotionStage.SIMULATION,
    PromotionStage.REPLAY,
    PromotionStage.READ_ONLY_BROKER_CONNECTION,
    PromotionStage.PAPER_TRADING,
    PromotionStage.SHADOW_TRADING,
    PromotionStage.MICRO_LIVE,
    PromotionStage.FULL_LIVE,
]

# Route Capability Matrix definition (TRD-FR-182)
ROUTE_CAPABILITY_MATRIX = {
    TradingRoute.SIM: {
        PromotionStage.OFFLINE_TEST: {
            MutationCapability.PACKAGED_ONLY,
            MutationCapability.READ_ONLY,
        },
        PromotionStage.SIMULATION: {
            MutationCapability.PACKAGED_ONLY,
            MutationCapability.READ_ONLY,
        },
        PromotionStage.REPLAY: {
            MutationCapability.PACKAGED_ONLY,
            MutationCapability.READ_ONLY,
        },
    },
    TradingRoute.PAPER: {
        PromotionStage.PAPER_TRADING: {MutationCapability.PAPER_ONLY},
    },
    TradingRoute.SHADOW: {
        PromotionStage.SHADOW_TRADING: {MutationCapability.SHADOW_ONLY},
    },
    TradingRoute.LIVE: {
        PromotionStage.READ_ONLY_BROKER_CONNECTION: {MutationCapability.READ_ONLY},
        PromotionStage.MICRO_LIVE: {MutationCapability.MICRO_LIVE},
        PromotionStage.FULL_LIVE: {MutationCapability.FULL_LIVE},
    },
}


def validate_route_stage_capability(
    route: TradingRoute,
    stage: PromotionStage,
    capability: MutationCapability,
) -> None:
    """Validate route, promotion stage, and mutation capability compatibility.

    Enforces the Route Capability Matrix (TRD-FR-182).

    Args:
        route: The requested trading route.
        stage: The requested promotion stage.
        capability: The requested mutation capability.

    Raises:
        TradingValidationError: If the combination is invalid.
    """
    route_val = route.value if hasattr(route, "value") else str(route)
    stage_val = stage.value if hasattr(stage, "value") else str(stage)
    capability_val = (
        capability.value if hasattr(capability, "value") else str(capability)
    )

    logger.info(
        "Validating compatibility of route={}, stage={}, capability={}.",
        route_val,
        stage_val,
        capability_val,
    )

    allowed_stages = ROUTE_CAPABILITY_MATRIX.get(route)
    if allowed_stages is None:
        logger.error("Unknown route: {}", route_val)
        msg = f"Route {route_val} is not configured in the capability matrix."
        raise TradingValidationError(msg)

    allowed_capabilities = allowed_stages.get(stage)
    if allowed_capabilities is None:
        logger.error("Stage {} not allowed for route {}.", stage_val, route_val)
        msg = f"Stage {stage_val} is not allowed for route {route_val}."
        raise TradingValidationError(msg)

    if capability not in allowed_capabilities:
        logger.error(
            "Capability {} not allowed for route {} and stage {}.",
            capability_val,
            route_val,
            stage_val,
        )
        msg = (
            f"Capability {capability_val} is not allowed for route "
            f"{route_val} and stage {stage_val}."
        )
        raise TradingValidationError(msg)

    logger.debug(
        "Route capability validation passed: route={}, stage={}, capability={}.",
        route_val,
        stage_val,
        capability_val,
    )


def evaluate_promotion_stage_gate(
    *,
    request: TradingRequestEnvelope,
) -> GateStepResult:
    """Evaluate the route/promotion stage compatibility check (Gate 3).

    Args:
        request: The incoming trading request envelope.

    Returns:
        GateStepResult: The gate evaluation outcome.
    """
    logger.info(
        "Evaluating promotion stage gate (Gate 3) for request {}.",
        request.request_id,
    )
    try:
        validate_route_stage_capability(
            route=request.route,
            stage=request.promotion_stage,
            capability=request.mutation_capability,
        )
    except TradingValidationError as exc:
        logger.warning(
            "Promotion stage gate blocked for request {}: {}.",
            request.request_id,
            str(exc),
        )
        return blocked_step(
            gate=GateName.PROMOTION_STAGE,
            reason_code="VALIDATION_FAILED",
            message=str(exc),
        )

    logger.info("Promotion stage gate passed for request {}.", request.request_id)
    return passed_step(gate=GateName.PROMOTION_STAGE)


def compute_canonical_promotion_hash(
    *,
    strategy_id: str,
    current_stage: PromotionStage,
    target_stage: PromotionStage,
) -> str:
    """Compute canonical hash of promotion request parameters (TRD-FR-183).

    Args:
        strategy_id: Strategy identifier.
        current_stage: Current promotion stage.
        target_stage: Target promotion stage.

    Returns:
        str: SHA-256 hex digest of the canonical promotion parameters.
    """
    logger.info("Computing canonical promotion hash for {}.", strategy_id)
    payload = {
        "strategy_id": strategy_id,
        "current_stage": current_stage.value,
        "target_stage": target_stage.value,
    }
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    logger.debug("Computed canonical promotion hash: {}.", digest)
    return digest


def _get_transition_indices(
    current_stage: PromotionStage,
    target_stage: PromotionStage,
) -> tuple[int, int]:
    """Helper to check sequence membership and fetch stage indices."""
    if current_stage not in PROMOTION_SEQUENCE:
        current_val = (
            current_stage.value
            if hasattr(current_stage, "value")
            else str(current_stage)
        )
        msg = f"Invalid current stage: {current_val}"
        raise TradingValidationError(msg)
    if target_stage not in PROMOTION_SEQUENCE:
        target_val = (
            target_stage.value if hasattr(target_stage, "value") else str(target_stage)
        )
        msg = f"Invalid target stage: {target_val}"
        raise TradingValidationError(msg)

    return (
        PROMOTION_SEQUENCE.index(current_stage),
        PROMOTION_SEQUENCE.index(target_stage),
    )


def _check_prerequisites(
    *,
    risk_policy_ok: bool,
    reconciliation_state_ok: bool,
    audit_sinks_ok: bool,
) -> None:
    """Helper to verify that all system preconditions are met."""
    if not risk_policy_ok:
        logger.error("Risk policy prerequisites not met for promotion.")
        raise TradingValidationError("Risk policy prerequisites are not fully met.")

    if not reconciliation_state_ok:
        logger.error("Reconciliation state not resolved for promotion.")
        raise TradingValidationError("Reconciliation state is unresolved or unhealthy.")

    if not audit_sinks_ok:
        logger.error("Audit sinks are not healthy for promotion.")
        raise TradingValidationError("Audit sinks are unhealthy.")


def _verify_transition_approvals(
    *,
    strategy_id: str,
    current_stage: PromotionStage,
    target_stage: PromotionStage,
    approvals: tuple[OperatorApprovalToken, ...],
    clock: Clock,
) -> None:
    """Helper to validate operator approval signatures."""
    if not approvals:
        logger.error("No operator approvals provided for promotion.")
        raise TradingValidationError(
            "Strategies cannot self-promote. Operator approval is required."
        )

    expected_hash = compute_canonical_promotion_hash(
        strategy_id=strategy_id,
        current_stage=current_stage,
        target_stage=target_stage,
    )
    expected_scope = ApprovalScope(strategy_id=strategy_id)
    expected_action = f"promote_to_{target_stage.value}"

    for token in approvals:
        if token.governed_action_id != expected_action:
            logger.error(
                "Mismatched action ID in approval: expected {}, got {}.",
                expected_action,
                token.governed_action_id,
            )
            msg = f"Mismatched approval token action ID. Expected {expected_action}."
            raise TradingValidationError(msg)

    now = clock.now_utc()
    if target_stage is PromotionStage.FULL_LIVE:
        logger.info("Promoting to full_live. Evaluating dual-operator approval.")
        validate_dual_operator_approval(
            tokens=approvals,
            now=now,
            expected_request_hash=expected_hash,
            expected_scope=expected_scope,
        )
    else:
        logger.info(
            "Promoting to {}. Evaluating single-operator approval.",
            target_stage.value,
        )
        validate_operator_approval(
            token=approvals[0],
            now=now,
            expected_request_hash=expected_hash,
            expected_scope=expected_scope,
        )


def validate_promotion_transition(
    *,
    strategy_id: str,
    current_stage: PromotionStage,
    target_stage: PromotionStage,
    approvals: tuple[OperatorApprovalToken, ...],
    clock: Clock,
    risk_policy_ok: bool,
    reconciliation_state_ok: bool,
    audit_sinks_ok: bool,
) -> None:
    """Validate a promotion ladder stage transition (TRD-FR-183, TRD-FR-184).

    Args:
        strategy_id: Strategy identifier.
        current_stage: Current promotion stage.
        target_stage: Requested target promotion stage.
        approvals: Operator approval tokens presented.
        clock: Injected clock.
        risk_policy_ok: True if risk policy prerequisites are met.
        reconciliation_state_ok: True if reconciliation state is healthy.
        audit_sinks_ok: True if audit sinks are healthy.

    Raises:
        TradingValidationError: If any validation check or prerequisite fails.
        TradingMappedError: If approval validation fails.
    """
    current_val = (
        current_stage.value if hasattr(current_stage, "value") else str(current_stage)
    )
    target_val = (
        target_stage.value if hasattr(target_stage, "value") else str(target_stage)
    )

    logger.info(
        "Validating promotion transition for strategy {} from {} to {}.",
        strategy_id,
        current_val,
        target_val,
    )

    current_idx, target_idx = _get_transition_indices(current_stage, target_stage)

    # 1. No-op transitions
    if current_idx == target_idx:
        logger.info("Promotion transition is a no-op (stage unchanged).")
        return

    # 2. Demotions are allowed to skip steps and do not require approval
    if target_idx < current_idx:
        logger.info("Transition is a demotion. No approvals required.")
        return

    # 3. Promotions cannot skip steps (TRD-FR-183)
    if target_idx > current_idx + 1:
        logger.error(
            "Promotion skips steps: {} -> {}.",
            current_stage.value,
            target_stage.value,
        )
        msg = (
            f"Promotion transitions cannot skip steps. Next allowed stage "
            f"is {PROMOTION_SEQUENCE[current_idx + 1].value}."
        )
        raise TradingValidationError(msg)

    # 4. Check prerequisites (TRD-FR-184)
    _check_prerequisites(
        risk_policy_ok=risk_policy_ok,
        reconciliation_state_ok=reconciliation_state_ok,
        audit_sinks_ok=audit_sinks_ok,
    )

    # 5. Verify operator approvals (TRD-FR-183, TRD-FR-184)
    _verify_transition_approvals(
        strategy_id=strategy_id,
        current_stage=current_stage,
        target_stage=target_stage,
        approvals=approvals,
        clock=clock,
    )

    logger.info("Promotion transition validation successful.")
