"""Deterministic classification of a no-trade outcome as safe or failed."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from app.composition.logging import get_logger
from app.services.risk.contracts.responses import guard_risk_boundary
from app.services.risk.no_trade_state.models import build_no_trade_outcome

logger = get_logger(__name__)

_MANDATORY_GATE_RULES = frozenset(
    {
        "freshness",
        "consistency",
        "kill_switch",
        "emergency_state",
        "drawdown",
        "drawdown_state",
        "daily_loss",
        "total_loss",
        "margin_utilization",
        "effective_leverage",
        "historical_var",
        "historical_cvar",
        "correlation",
        "session",
        "calendar",
        "regime_evidence",
        "mandate",
        "single_day_profit_share",
    }
)


def _classify(failed_rule_ids: Sequence[str]) -> str:
    """Classify failed rule identities as a safe stand-down or failed gameplay.

    Args:
        failed_rule_ids: Non-empty ordered failed rule identities.

    Returns:
        ``"safe_stand_down"`` when every failed rule is a registered
        mandatory gate; ``"failed_gameplay"`` otherwise, including any
        unregistered rule identity (fail closed — never infer a safe
        stand-down for an unrecognized reason).
    """
    if all(rule_id in _MANDATORY_GATE_RULES for rule_id in failed_rule_ids):
        return "safe_stand_down"
    return "failed_gameplay"


@guard_risk_boundary(risk_level="low", read_only=True)
def classify_no_trade_outcome(
    decision_id: str,
    failed_rule_ids: Sequence[str],
    *,
    now: datetime,
) -> dict[str, object]:
    """Classify a rejected setup as a safe stand-down or failed gameplay.

    Distinguishes a correctly-identified no-trade day (every failed rule was
    a mandatory Risk gate — a passing operational outcome) from a rejection
    caused by an avoidable execution mistake (e.g. an invalid stop
    placement or a concentration breach — a failed operational outcome).

    Args:
        decision_id: Identity of the originating Risk decision.
        failed_rule_ids: Non-empty ordered failed rule identities from the
            originating decision or check results.
        now: Explicit aware-UTC classification time.

    Returns:
        JSON-safe ``NoTradeOutcome v1`` mapping.

    Raises:
        RiskDomainError: If ``failed_rule_ids`` is empty or identities are
            invalid.
    """
    logger.info("Classifying Risk no-trade outcome for decision: %s", decision_id)
    ordered = tuple(failed_rule_ids)
    outcome_kind = _classify(ordered)
    rationale = (
        "every failed check is a registered mandatory Risk gate"
        if outcome_kind == "safe_stand_down"
        else "at least one failed check is an avoidable execution rule"
    )
    return build_no_trade_outcome(
        decision_id=decision_id,
        outcome_kind=outcome_kind,
        failed_rule_ids=ordered,
        rationale=rationale,
        evaluated_at=now,
    )


__all__ = ["classify_no_trade_outcome"]
