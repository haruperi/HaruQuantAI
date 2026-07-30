"""Shared exact-authority validation for governed Trading mutations."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.services.risk import get_decision_state
from app.services.trading.contracts import TradingError, TradingRequest
from app.utils import get_logger

logger = get_logger(__name__)

ActionPolicyVerdict = Any
KillSwitchState = Any
RiskDecisionPackage = Any


def validate_action_policy(
    request: TradingRequest,
    verdict: ActionPolicyVerdict | None,
    now: datetime,
) -> ActionPolicyVerdict:
    """Validate exact current Risk action-policy authority.

    Args:
        request: Governed Trading request.
        verdict: Current Risk-owned action-policy verdict.
        now: Current injected UTC time.

    Returns:
        Exact valid verdict.

    Raises:
        TradingError: If verdict identity, scope, state, or lifetime fails.
    """
    logger.debug("Running Trading action-policy authority validation")
    valid = verdict is not None and (
        verdict.verdict_id == request.action_policy_verdict_id
        and verdict.action == request.action
        and verdict.decision_id == request.risk_decision_id
        and verdict.request_id == request.request_id
        and verdict.workflow_id == request.workflow_id
        and verdict.correlation_id == request.correlation_id
        and verdict.scope.get("account_id") == request.account_id
        and verdict.allowed
        and verdict.issued_at <= now < verdict.expires_at
    )
    if not valid or verdict is None:
        raise TradingError("GATE_BLOCKED", "Action-policy authority is invalid")
    optional_scope = {
        "portfolio_id": request.portfolio_id,
        "strategy_id": request.strategy_id,
        "symbol": request.symbol,
    }
    if any(
        key in verdict.scope and verdict.scope[key] != value
        for key, value in optional_scope.items()
    ):
        raise TradingError("SCOPE_MISMATCH", "Action-policy scope is mismatched")
    return verdict


def validate_risk_authority(
    request: TradingRequest,
    decision: RiskDecisionPackage | None,
    now: datetime,
) -> RiskDecisionPackage:
    """Validate exact current Risk approval and token binding.

    Args:
        request: Governed Trading request.
        decision: Current Risk-owned decision package.
        now: Current injected UTC time.

    Returns:
        Exact valid Risk decision.

    Raises:
        TradingError: If decision, size, token, trace, or lifetime fails.
    """
    logger.debug("Running Trading Risk-decision authority validation")
    if decision is None or decision.token is None:
        raise TradingError("GATE_BLOCKED", "Real Risk approval is required")
    token = decision.token
    valid = (
        decision.decision_id == request.risk_decision_id
        and decision.intent_id == request.intent_id
        and decision.state is get_decision_state("APPROVE")
        and decision.approved_size == request.quantity
        and decision.request_id == request.request_id
        and decision.workflow_id == request.workflow_id
        and decision.correlation_id == request.correlation_id
        and decision.issued_at <= now < decision.expires_at
        and token.token_id == request.approval_token_ref
        and token.decision_id == decision.decision_id
        and token.action == request.action
        and token.request_id == request.request_id
        and token.workflow_id == request.workflow_id
        and token.correlation_id == request.correlation_id
        and token.scope.get("account_id") == request.account_id
        and token.issued_at <= now < token.expires_at
    )
    if not valid:
        raise TradingError("GATE_BLOCKED", "Risk approval is invalid or stale")
    return decision


def _required_kill_switch_scopes(
    request: TradingRequest,
) -> dict[tuple[str, tuple[tuple[str, str], ...]], None]:
    """Build exact applicable kill-switch scope keys.

    Args:
        request: Governed Trading request.

    Returns:
        Exact required hierarchy keys.
    """
    required: dict[tuple[str, tuple[tuple[str, str], ...]], None] = {
        ("global", ()): None,
        ("strategy", (("strategy_id", request.strategy_id),)): None,
    }
    if request.portfolio_id is not None:
        required[("portfolio", (("portfolio_id", request.portfolio_id),))] = None
    if request.symbol is not None:
        required[("symbol", (("symbol", request.symbol),))] = None
    return required


def validate_kill_switch_hierarchy(
    request: TradingRequest,
    states: Sequence[KillSwitchState],
    max_staleness_seconds: Decimal,
    now: datetime,
    *,
    allowed_active_levels: frozenset[str] = frozenset(),
) -> None:
    """Validate every exact applicable Risk kill-switch scope.

    Args:
        request: Governed Trading request defining the exact hierarchy.
        states: Risk-owned scope states.
        max_staleness_seconds: Positive exact evidence age bound.
        now: Current injected UTC time.
        allowed_active_levels: Scope levels permitted to remain active for an
            authorized clearance operation.

    Raises:
        TradingError: If scope evidence is missing, duplicated, unrelated, active,
            unknown, future-dated, or stale.
    """
    logger.debug("Running Trading kill-switch hierarchy authority validation")
    if (
        not isinstance(max_staleness_seconds, Decimal)
        or not max_staleness_seconds.is_finite()
        or max_staleness_seconds <= 0
    ):
        raise TradingError(
            "CONFIGURATION_INVALID", "Kill-switch staleness bound is invalid"
        )
    actual = [
        (state.scope_level, tuple(sorted(state.scope.items()))) for state in states
    ]
    required = set(_required_kill_switch_scopes(request))
    if len(actual) != len(set(actual)) or set(actual) != required:
        raise TradingError(
            "KILL_SWITCH_UNKNOWN",
            "Exact applicable kill-switch hierarchy is unproven",
        )
    if any(state.state == "unknown" for state in states):
        raise TradingError("KILL_SWITCH_UNKNOWN", "Kill-switch state is unproven")
    if any(
        state.state == "active" and state.scope_level not in allowed_active_levels
        for state in states
    ):
        raise TradingError("KILL_SWITCH_ACTIVE", "Kill-switch hierarchy is active")
    if any(
        state.updated_at > now
        or Decimal(str((now - state.updated_at).total_seconds()))
        > max_staleness_seconds
        for state in states
    ):
        raise TradingError(
            "KILL_SWITCH_STALE",
            "Kill-switch hierarchy evidence is stale and cannot prove clearance",
        )


__all__ = [
    "validate_action_policy",
    "validate_kill_switch_hierarchy",
    "validate_risk_authority",
]
