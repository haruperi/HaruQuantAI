"""Risk governance enums and catalogs.

Defines all deterministic string enums, ordered severity rankings, reason codes,
and helper functions used throughout the Risk Governance domain.
"""

from __future__ import annotations

from enum import StrEnum

from app.utils.logger import logger


class RiskDecisionStatus(StrEnum):
    """Canonical outcomes of the risk review process."""

    APPROVE = "approve"
    REDUCE_SIZE = "reduce_size"
    REJECT = "reject"
    BLOCK = "block"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    NEEDS_APPROVAL = "needs_approval"
    HALT_STRATEGY = "halt_strategy"
    HALT_ALL = "halt_all"


class RiskMode(StrEnum):
    """Execution mode of the trading system."""

    OFFLINE = "offline"
    SIMULATION = "simulation"
    PAPER = "paper"
    SHADOW = "shadow"
    LIVE_READONLY = "live_readonly"
    MICRO_LIVE = "micro_live"
    FULL_LIVE = "full_live"


class RiskAction(StrEnum):
    """Governed actions requiring risk approval."""

    EXECUTE_TRADE = "execute_trade"
    ALLOCATE_CAPITAL = "allocate_capital"
    ADMIT_STRATEGY = "admit_strategy"
    PROMOTE_MODE = "promote_mode"


class RiskSeverity(StrEnum):
    """Severity levels for violations or events."""

    INFO = "info"
    WARNING = "warning"
    SOFT_BREACH = "soft_breach"
    HARD_BREACH = "hard_breach"
    CRITICAL_BREACH = "critical_breach"
    EMERGENCY_HALT = "emergency_halt"


class RiskReasonCode(StrEnum):
    """Deterministic reasons for decisions."""

    OK = "OK"
    NEWS_BLACKOUT = "NEWS_BLACKOUT"
    ROLLOVER_BLACKOUT = "ROLLOVER_BLACKOUT"
    KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    DRAWDOWN_BREACH = "DRAWDOWN_BREACH"
    DAILY_LOSS_BREACH = "DAILY_LOSS_BREACH"
    LEVERAGE_BREACH = "LEVERAGE_BREACH"
    MARGIN_BREACH = "MARGIN_BREACH"
    CONCENTRATION_BREACH = "CONCENTRATION_BREACH"
    CURRENCY_BREACH = "CURRENCY_BREACH"
    CORRELATION_BREACH = "CORRELATION_BREACH"
    VAR_BREACH = "VAR_BREACH"
    ES_BREACH = "ES_BREACH"
    STRESS_BREACH = "STRESS_BREACH"
    SLIPPAGE_BREACH = "SLIPPAGE_BREACH"
    SPREAD_BREACH = "SPREAD_BREACH"
    FREQUENCY_BREACH = "FREQUENCY_BREACH"
    INVALID_INPUT = "INVALID_INPUT"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
    PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED = "PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED"
    ALLOCATION_LIMIT_BREACH = "ALLOCATION_LIMIT_BREACH"
    LIFECYCLE_GATES_BREACH = "LIFECYCLE_GATES_BREACH"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"

    @property
    def description(self) -> str:
        """Get the stable description for the reason code.

        Returns:
            str: Description of the reason code.
        """
        descriptions = {
            RiskReasonCode.OK: "Evaluation passed successfully.",
            RiskReasonCode.NEWS_BLACKOUT: (
                "Trading blocked due to news event blackout window."
            ),
            RiskReasonCode.ROLLOVER_BLACKOUT: (
                "Trading blocked due to broker-midnight rollover window."
            ),
            RiskReasonCode.KILL_SWITCH_ACTIVE: (
                "System-wide or strategy-specific kill switch is active."
            ),
            RiskReasonCode.STALE_EVIDENCE: "Required evidence is stale or not trusted.",
            RiskReasonCode.DRAWDOWN_BREACH: "Total drawdown limit breached.",
            RiskReasonCode.DAILY_LOSS_BREACH: "Daily loss limit breached.",
            RiskReasonCode.LEVERAGE_BREACH: "Effective leverage limit breached.",
            RiskReasonCode.MARGIN_BREACH: "Margin utilization limit breached.",
            RiskReasonCode.CONCENTRATION_BREACH: "Asset concentration limit breached.",
            RiskReasonCode.CURRENCY_BREACH: "Currency exposure limit breached.",
            RiskReasonCode.CORRELATION_BREACH: "Portfolio correlation limit breached.",
            RiskReasonCode.VAR_BREACH: "Value-at-Risk limit breached.",
            RiskReasonCode.ES_BREACH: "Expected Shortfall limit breached.",
            RiskReasonCode.STRESS_BREACH: "Stress testing scenario limit breached.",
            RiskReasonCode.SLIPPAGE_BREACH: "Slippage tolerance limit breached.",
            RiskReasonCode.SPREAD_BREACH: "Spread tolerance limit breached.",
            RiskReasonCode.FREQUENCY_BREACH: "Order frequency limit breached.",
            RiskReasonCode.INVALID_INPUT: "Input request validation failed.",
            RiskReasonCode.UNEXPECTED_ERROR: (
                "An unexpected error occurred during risk evaluation."
            ),
            RiskReasonCode.PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED: (
                "Double spend blocked due to pending approval."
            ),
            RiskReasonCode.ALLOCATION_LIMIT_BREACH: (
                "Strategy allocation limit breached."
            ),
            RiskReasonCode.LIFECYCLE_GATES_BREACH: "Lifecycle readiness check failed.",
            RiskReasonCode.APPROVAL_REQUIRED: (
                "Governed approval is required for this action."
            ),
        }
        return descriptions.get(self, "Unknown reason code.")


class KillSwitchStateEnum(StrEnum):
    """Safety kill-switch states.

    States progress: INACTIVE -> TRIGGERED -> ACTIVE -> PENDING_RESUME -> INACTIVE.
    LOCKED is a special terminal state requiring admin/compliance intervention.
    UNKNOWN signals an indeterminate state and must always fail closed.
    """

    INACTIVE = "inactive"
    ACTIVE = "active"
    LOCKED = "locked"
    UNKNOWN = "unknown"
    TRIGGERED = "triggered"
    PENDING_RESUME = "pending_resume"


class KillSwitchReason(StrEnum):
    """Reason codes explaining why a kill switch was triggered."""

    MANUAL_HALT = "manual_halt"
    DAILY_LOSS_BREACH = "daily_loss_breach"
    DRAWDOWN_BREACH = "drawdown_breach"
    AUDIT_FAILURE = "audit_failure"
    EXTREME_SPREAD = "extreme_spread"
    PORTFOLIO_UNRECONCILED = "portfolio_unreconciled"
    BROKER_DISCONNECT = "broker_disconnect"
    MARGIN_EMERGENCY = "margin_emergency"


def list_risk_reason_codes() -> tuple[RiskReasonCode, ...]:
    """Returns the stable reason-code catalogue in deterministic order.

    Returns:
        tuple[RiskReasonCode, ...]: Stable list of all risk reason codes.
    """
    codes = tuple(RiskReasonCode)
    logger.info("Listed risk reason codes catalog, total count: %d", len(codes))
    return codes


def risk_severity_rank(severity: RiskSeverity) -> int:
    """Returns stable ordering rank for aggregation and primary-failure selection.

    Args:
        severity: The risk severity level to rank.

    Returns:
        int: Severity rank (higher values represent higher severity).
    """
    ranks = {
        RiskSeverity.INFO: 0,
        RiskSeverity.WARNING: 1,
        RiskSeverity.SOFT_BREACH: 2,
        RiskSeverity.HARD_BREACH: 3,
        RiskSeverity.CRITICAL_BREACH: 4,
        RiskSeverity.EMERGENCY_HALT: 5,
    }
    rank = ranks.get(severity, -1)
    logger.debug("Resolved severity rank for %s: %d", severity, rank)
    return rank
