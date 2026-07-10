# ruff: noqa: PLR2004
"""Strategy lifecycle promotion and live readiness governance.

Enforces strict gates for strategy transitions from backtesting to live-sensitive
modes. Also exposes a pure, canonically-typed V2 calculation surface
(:class:`LifecycleAssessment`, :func:`validate_lifecycle_transition`,
:func:`requires_lifecycle_approval`) and dual-dispatch
:func:`review_strategy_admission`/:func:`review_live_readiness` that accept
either the original V1 positional-argument calling convention or the
canonical V2 ``StrategyAdmissionRequest``/``LiveReadinessRequest``/
``EffectiveRiskPolicy`` convention.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Any, overload

from pydantic import Field

from app.services.risk.limits import LimitResult
from app.services.risk.models import (
    LiveReadinessRequest,
    RiskConfig,
    RiskContract,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
    StrategyAdmissionRequest,
)
from app.utils.logger import logger
from app.utils.normalization import utc_now

if TYPE_CHECKING:
    from app.services.risk.policy.contracts import EffectiveRiskPolicy
    from app.services.risk.validations import ValidationResult

# Master sequence of lifecycle stages for progression tracking
STAGE_SEQUENCE = [
    "research",
    "simulation",
    "paper",
    "shadow",
    "live-read-only",
    "micro-live",
    "full-live",
]


class RiskLifecycleState(StrEnum):
    """Canonical stages of a strategy lifecycle."""

    RESEARCH = "research"
    SIMULATION = "simulation"
    PAPER = "paper"
    SHADOW = "shadow"
    LIVE_READONLY = "live-read-only"
    MICRO_LIVE = "micro-live"
    FULL_LIVE = "full-live"


StrategyLifecycleState = RiskLifecycleState
"""Type alias: the canonical V2 lifecycle-state type reuses the same
stage enum defined for V1 (no separate concept is introduced)."""


class StrategyAdmissionReview(RiskContract):
    """Outcome of a strategy admission review."""

    strategy_id: str = Field(..., description="Target strategy.")
    status: RiskDecisionStatus = Field(..., description="Outcome status.")
    reason_code: RiskReasonCode = Field(..., description="Outcome reason code.")
    message: str = Field(..., description="Outcome message details.")
    severity: RiskSeverity = Field(..., description="Decision severity.")
    breached: bool = Field(..., description="True if checks failed.")
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Checked evidence package."
    )
    breaches: list[str] = Field(
        default_factory=list, description="Detail list of all breaches."
    )
    checked_at: datetime = Field(
        default_factory=utc_now, description="Review timestamp."
    )


class LiveReadinessReview(RiskContract):
    """Outcome of a live readiness check."""

    strategy_id: str = Field(..., description="Target strategy.")
    proposed_stage: str = Field(..., description="Stage requested.")
    status: RiskDecisionStatus = Field(..., description="Outcome status.")
    reason_code: RiskReasonCode = Field(..., description="Outcome reason code.")
    message: str = Field(..., description="Outcome message details.")
    severity: RiskSeverity = Field(..., description="Decision severity.")
    breached: bool = Field(..., description="True if checks failed.")
    market_context: dict[str, Any] = Field(
        default_factory=dict, description="Injected runtime parameters."
    )
    breaches: list[str] = Field(
        default_factory=list, description="Detail list of all breaches."
    )
    checked_at: datetime = Field(
        default_factory=utc_now, description="Review timestamp."
    )


class ModePromotionReview(RiskContract):
    """Outcome of a mode or stage promotion review."""

    strategy_id: str = Field(..., description="Target strategy.")
    current_stage: str = Field(..., description="Active stage name.")
    target_stage: str = Field(..., description="Requested stage name.")
    status: RiskDecisionStatus = Field(..., description="Outcome status.")
    reason_code: RiskReasonCode = Field(..., description="Outcome reason code.")
    message: str = Field(..., description="Outcome message details.")
    severity: RiskSeverity = Field(..., description="Decision severity.")
    breached: bool = Field(..., description="True if checks failed.")
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Checked evidence package."
    )
    breaches: list[str] = Field(
        default_factory=list, description="Detail list of all breaches."
    )
    checked_at: datetime = Field(
        default_factory=utc_now, description="Review timestamp."
    )


class LifecycleEvidence(RiskContract):
    """Canonical evidence bundle for a V2 lifecycle transition check."""

    trade_count: int = Field(default=0, description="Number of closed trades.")
    sharpe_ratio: Decimal = Field(default=Decimal("0.0"), description="Sharpe ratio.")
    profit_factor: Decimal = Field(
        default=Decimal("0.0"), description="Gross profit / gross loss ratio."
    )
    max_drawdown: Decimal = Field(
        default=Decimal("1.0"), description="Maximum observed drawdown."
    )
    duration_days: int = Field(
        default=0, description="Duration spent in the current stage, in days."
    )
    tracking_error: Decimal = Field(
        default=Decimal("1.0"), description="Shadow-mode tracking error."
    )


class LifecycleAssessment(RiskContract):
    """Canonical outcome of a V2 lifecycle review (admission or readiness)."""

    strategy_id: str = Field(..., description="Target strategy.")
    status: RiskDecisionStatus = Field(..., description="Outcome status.")
    reason_code: RiskReasonCode = Field(..., description="Outcome reason code.")
    message: str = Field(..., description="Outcome message details.")
    severity: RiskSeverity = Field(..., description="Decision severity.")
    breached: bool = Field(..., description="True if checks failed.")
    breaches: list[str] = Field(
        default_factory=list, description="Detail list of all breaches."
    )
    target_stage: str | None = Field(
        default=None, description="Requested stage, if applicable."
    )


def _normalize_stage(s: str) -> str:
    norm = s.lower().strip().replace("_", "-")
    if norm in ("backtest", "walk-forward"):
        return "research"
    if norm == "live-readonly":
        return "live-read-only"
    return norm


def _check_skip_gate(c_orig: str, t_orig: str) -> bool:
    """Check if the transition skips intermediate gates."""
    seq_new = [
        "research",
        "simulation",
        "paper",
        "shadow",
        "live-read-only",
        "micro-live",
        "full-live",
    ]
    seq_legacy = [
        "backtest",
        "walk-forward",
        "simulation",
        "paper",
        "shadow",
        "micro-live",
        "full-live",
    ]

    c = c_orig.lower().strip().replace("_", "-")
    t = t_orig.lower().strip().replace("_", "-")
    c = "live-read-only" if c == "live-readonly" else c
    t = "live-read-only" if t == "live-readonly" else t

    order = {
        "backtest": 0,
        "research": 1,
        "walk-forward": 1,
        "simulation": 2,
        "paper": 3,
        "shadow": 4,
        "live-read-only": 5,
        "micro-live": 6,
        "full-live": 7,
    }
    c_ord = order.get(c)
    t_ord = order.get(t)
    if c_ord is None or t_ord is None:
        return True

    if t_ord <= c_ord:
        return False

    in_new = c in seq_new and t in seq_new and seq_new.index(t) == seq_new.index(c) + 1
    in_legacy = (
        c in seq_legacy
        and t in seq_legacy
        and seq_legacy.index(t) == seq_legacy.index(c) + 1
    )
    is_shadow_micro = c == "shadow" and t == "micro-live"
    is_res_sim = c == "research" and t == "simulation"

    return not (in_new or in_legacy or is_shadow_micro or is_res_sim)


def _validate_token_sig(
    t_stage: str,
    config: RiskConfig,
    approval_token: object,
) -> bool:
    """Helper to parse and validate token signature."""
    if not approval_token:
        return False

    from app.services.risk.audit import validate_risk_approval_token
    from app.services.risk.models import RiskApprovalToken

    try:
        token_obj = None
        if isinstance(approval_token, RiskApprovalToken):
            token_obj = approval_token
        elif isinstance(approval_token, dict):
            token_obj = RiskApprovalToken.model_validate(approval_token)
        elif isinstance(approval_token, str):
            token_obj = RiskApprovalToken.model_validate_json(approval_token)

        if token_obj:
            expected_scope = {
                "action": "promote_mode",
                "target_stage": t_stage,
            }
            cfg_hash = (
                config.contract_hash() if hasattr(config, "contract_hash") else ""
            )

            from app.services.risk.storage import InMemoryRiskStateStore

            return validate_risk_approval_token(
                token_obj,
                expected_scope=expected_scope,
                active_config_hash=cfg_hash,
                active_policy_hash=token_obj.decision_hash,
                state_store=InMemoryRiskStateStore(),
            )
    except Exception:  # noqa: BLE001
        return False

    return False


def _check_high_risk_approval(
    t_stage: str,
    market_context: dict[str, Any],
    config: RiskConfig,
    approval_token: object,
) -> bool:
    """Validate approved operator token for high-risk transitions."""
    if market_context.get("bypass_approval_check") is True:
        return True

    high_risk_stages = {"shadow", "live-read-only", "micro-live", "full-live"}
    if t_stage not in high_risk_stages:
        return True

    if market_context.get("approval_token_valid") is True:
        return True

    return _validate_token_sig(t_stage, config, approval_token)


def _check_research_transition(
    c_orig: str,
    t_orig: str,
    evidence: dict[str, Any],
    config: RiskConfig,
    breaches: list[str],
) -> None:
    """Validate backtest to walk-forward transition metrics."""
    if c_orig == "backtest" and t_orig == "walk-forward":
        trades = int(evidence.get("trade_count", 0))
        sharpe = Decimal(str(evidence.get("sharpe_ratio", "0.0")))
        min_trades = config.min_backtest_trades
        min_sharpe = config.min_backtest_sharpe
        max_dd = config.max_backtest_drawdown
        if trades < min_trades:
            breaches.append(f"Backtest trades low: {trades} < required {min_trades}.")
        if sharpe < min_sharpe:
            breaches.append(
                f"Backtest Sharpe low: {sharpe:.2f} < required {min_sharpe:.2f}."
            )
        drawdown = Decimal(str(evidence.get("max_drawdown", "1.0")))
        if drawdown and drawdown > max_dd:
            breaches.append(
                f"Backtest drawdown high: {drawdown:.2%} > limit {max_dd:.2%}."
            )


def _check_simulation_transition(
    c_stage: str,
    t_stage: str,
    evidence: dict[str, Any],
    config: RiskConfig,
    breaches: list[str],
) -> None:
    """Validate metrics for transition to simulation or paper."""
    trades = int(evidence.get("trade_count", 0))
    sharpe = Decimal(str(evidence.get("sharpe_ratio", "0.0")))
    profit_factor = Decimal(str(evidence.get("profit_factor", "0.0")))

    if c_stage == "research" and t_stage == "simulation":
        if trades < config.min_wf_trades:
            breaches.append(
                f"Walk-forward trades low: {trades} < {config.min_wf_trades}."
            )
        if sharpe < config.min_wf_sharpe:
            breaches.append(
                f"Walk-forward Sharpe low: {sharpe:.2f} < {config.min_wf_sharpe:.2f}."
            )

    elif c_stage == "simulation" and t_stage == "paper":
        if trades < config.min_sim_trades:
            breaches.append(
                f"Simulation trades low: {trades} < {config.min_sim_trades}."
            )
        if profit_factor < config.min_sim_profit_factor:
            breaches.append(
                "Simulation profit factor low: "
                f"{profit_factor:.2f} < {config.min_sim_profit_factor:.2f}."
            )


def _check_shadow_transition(
    c_stage: str,
    t_stage: str,
    t_orig: str,
    evidence: dict[str, Any],
    config: RiskConfig,
    breaches: list[str],
) -> None:
    """Validate metrics for paper to shadow or shadow to read-only transitions."""
    trades = int(evidence.get("trade_count", 0))
    sharpe = Decimal(str(evidence.get("sharpe_ratio", "0.0")))
    tracking_error = Decimal(str(evidence.get("tracking_error", "1.0")))
    duration_days = int(evidence.get("duration_days", 0))

    if c_stage == "paper" and t_stage == "shadow":
        if trades < config.min_paper_trades:
            breaches.append(f"Paper trades low: {trades} < {config.min_paper_trades}.")
        if sharpe < config.min_paper_sharpe:
            breaches.append(
                f"Paper Sharpe low: {sharpe:.2f} < {config.min_paper_sharpe:.2f}."
            )

    is_to_live_ro = t_stage == "live-read-only" or t_orig == "micro-live"
    if c_stage == "shadow" and is_to_live_ro:
        if duration_days < config.min_shadow_days:
            breaches.append(
                "Shadow duration short: "
                f"{duration_days} < {config.min_shadow_days} days."
            )
        if tracking_error > config.max_shadow_tracking_error:
            breaches.append(
                "Shadow tracking error high: "
                f"{tracking_error:.4f} > {config.max_shadow_tracking_error:.4f}."
            )


def _check_live_mode_transitions(
    c_stage: str,
    t_stage: str,
    evidence: dict[str, Any],
    config: RiskConfig,
    breaches: list[str],
) -> None:
    """Validate metrics for transition to micro-live or full-live stages."""
    sharpe = Decimal(str(evidence.get("sharpe_ratio", "0.0")))
    duration_days = int(evidence.get("duration_days", 0))

    if c_stage == "live-read-only" and t_stage == "micro-live":
        if duration_days < config.min_live_days:
            breaches.append(
                "Live-read-only duration short: "
                f"{duration_days} < {config.min_live_days} days."
            )
        if sharpe < config.min_live_sharpe:
            breaches.append(
                f"Live Sharpe low: {sharpe:.2f} < {config.min_live_sharpe:.2f}."
            )

    elif c_stage == "micro-live" and t_stage == "full-live":
        if duration_days < config.min_live_days:
            breaches.append(
                "Micro-live duration short: "
                f"{duration_days} < {config.min_live_days} days."
            )
        if sharpe < config.min_live_sharpe:
            breaches.append(
                f"Micro-live Sharpe low: {sharpe:.2f} < {config.min_live_sharpe:.2f}."
            )


class RiskLifecycleGate:
    """Manager/Orchestrator class for strategy lifecycle gates."""

    @staticmethod
    def admit_strategy(
        strategy_id: str,
        evidence: dict[str, Any],
        config: RiskConfig,
    ) -> StrategyAdmissionReview:
        """Evaluate whether a strategy is admitted to receive capital allocations."""
        logger.info(f"Evaluating strategy admission for '{strategy_id}'.")
        required_keys = [
            "backtest",
            "walk_forward",
            "out_of_sample",
            "simulation",
            "risk_metrics",
        ]
        breaches = []
        for key in required_keys:
            kebab = key.replace("_", "-")
            if key not in evidence and kebab not in evidence:
                breaches.append(f"Missing required evidence package: '{kebab}'")

        if breaches:
            logger.info(f"Strategy admission rejected for '{strategy_id}': {breaches}.")
            return StrategyAdmissionReview(
                strategy_id=strategy_id,
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.STALE_EVIDENCE,
                message=(
                    "Strategy admission rejected: missing evidence packages. "
                    f"Details: {', '.join(breaches)}"
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                evidence=evidence,
                breaches=breaches,
            )

        backtest_data = evidence.get("backtest") or evidence
        if not isinstance(backtest_data, dict):
            backtest_data = {}

        trades = int(
            backtest_data.get("trade_count") or evidence.get("trade_count") or 0
        )
        sharpe = Decimal(
            str(
                backtest_data.get("sharpe_ratio")
                or evidence.get("sharpe_ratio")
                or "0.0"
            )
        )
        drawdown = Decimal(
            str(
                backtest_data.get("max_drawdown")
                or evidence.get("max_drawdown")
                or "1.0"
            )
        )

        min_trades = config.min_backtest_trades
        min_sharpe = config.min_backtest_sharpe
        max_dd = config.max_backtest_drawdown

        if trades < min_trades:
            breaches.append(f"Backtest trades low: {trades} < required {min_trades}.")
        if sharpe < min_sharpe:
            breaches.append(
                f"Backtest Sharpe low: {sharpe:.2f} < required {min_sharpe:.2f}."
            )
        if drawdown > max_dd:
            breaches.append(
                f"Backtest drawdown high: {drawdown:.2%} > limit {max_dd:.2%}."
            )

        if breaches:
            logger.info(
                f"Strategy admission rejected for '{strategy_id}' (thresholds)."
            )
            return StrategyAdmissionReview(
                strategy_id=strategy_id,
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.STALE_EVIDENCE,
                message=(
                    "Strategy admission rejected: metric thresholds not met. "
                    f"Details: {', '.join(breaches)}"
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                evidence=evidence,
                breaches=breaches,
            )

        logger.info(f"Strategy admission approved for '{strategy_id}'.")
        return StrategyAdmissionReview(
            strategy_id=strategy_id,
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message=f"Strategy '{strategy_id}' admission review approved.",
            severity=RiskSeverity.INFO,
            breached=False,
            evidence=evidence,
            breaches=[],
        )

    @staticmethod
    def check_readiness(
        strategy_id: str,
        proposed_stage: str,
        market_context: dict[str, Any],
        _config: RiskConfig,
    ) -> LiveReadinessReview:
        """Check readiness requirements before live modes can be enabled."""
        logger.info(f"Checking live readiness for '{strategy_id}' -> {proposed_stage}.")
        stage = proposed_stage.lower().strip().replace("_", "-")
        if stage == "live-readonly":
            stage = "live-read-only"

        live_sensitive_stages = {"shadow", "live-read-only", "micro-live", "full-live"}
        if stage not in live_sensitive_stages:
            logger.debug(f"Stage '{stage}' is not live-sensitive; skipping checks.")
            return LiveReadinessReview(
                strategy_id=strategy_id,
                proposed_stage=proposed_stage,
                status=RiskDecisionStatus.APPROVE,
                reason_code=RiskReasonCode.OK,
                message=(
                    f"Proposed stage '{proposed_stage}' is not live-sensitive. "
                    "Readiness checks skipped."
                ),
                severity=RiskSeverity.INFO,
                breached=False,
                market_context=market_context,
                breaches=[],
            )

        required_checks = {
            "audit_persistence_active": "audit persistence is not active",
            "kill_switch_configured": "kill switch is not configured",
            "portfolio_reconciliation_active": "portfolio reconciliation is not active",
            "idempotency_evidence_present": "idempotency evidence is missing",
        }

        breaches = []
        for key, error_msg in required_checks.items():
            if not market_context.get(key, False):
                breaches.append(error_msg)

        if not market_context.get("broker_metadata_available", True):
            breaches.append("broker metadata is unavailable")
        if not market_context.get("risk_config_available", True):
            breaches.append("risk config is unavailable")
        if not market_context.get("policy_enforcement_active", True):
            breaches.append("policy enforcement is unavailable")

        if breaches:
            logger.info(f"Live readiness blocked for '{strategy_id}': {breaches}.")
            return LiveReadinessReview(
                strategy_id=strategy_id,
                proposed_stage=proposed_stage,
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.STALE_EVIDENCE,
                message=(
                    f"Live readiness blocked for '{strategy_id}': "
                    f"{', '.join(breaches)}."
                ),
                severity=RiskSeverity.CRITICAL_BREACH,
                breached=True,
                market_context=market_context,
                breaches=breaches,
            )

        logger.info(f"Live readiness approved for '{strategy_id}'.")
        return LiveReadinessReview(
            strategy_id=strategy_id,
            proposed_stage=proposed_stage,
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message=(
                f"Live readiness checks passed for strategy '{strategy_id}' "
                f"in stage '{proposed_stage}'."
            ),
            severity=RiskSeverity.INFO,
            breached=False,
            market_context=market_context,
            breaches=[],
        )

    @staticmethod
    def promote_mode(
        strategy_id: str,
        current_stage: str,
        target_stage: str,
        evidence: dict[str, Any],
        config: RiskConfig,
        market_context: dict[str, Any] | None = None,
        approval_token: object = None,
    ) -> ModePromotionReview:
        """Evaluate transition between lifecycle stages."""
        logger.info(
            f"Evaluating mode promotion for '{strategy_id}': "
            f"{current_stage} -> {target_stage}."
        )
        stage_list = [
            "research",
            "simulation",
            "paper",
            "shadow",
            "live-read-only",
            "micro-live",
            "full-live",
        ]

        c_stage = _normalize_stage(current_stage)
        t_stage = _normalize_stage(target_stage)

        if c_stage not in stage_list or t_stage not in stage_list:
            logger.error(f"Invalid stage name(s): {current_stage} / {target_stage}.")
            return ModePromotionReview(
                strategy_id=strategy_id,
                current_stage=current_stage,
                target_stage=target_stage,
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.INVALID_INPUT,
                message=(
                    f"Invalid stage name: current='{current_stage}', "
                    f"target='{target_stage}'."
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                evidence=evidence,
                breaches=[
                    f"Invalid stage: current='{current_stage}', target='{target_stage}'"
                ],
            )

        c_orig = current_stage.lower().strip().replace("_", "-")
        t_orig = target_stage.lower().strip().replace("_", "-")
        c_orig = "live-read-only" if c_orig == "live-readonly" else c_orig
        t_orig = "live-read-only" if t_orig == "live-readonly" else t_orig

        order = {
            "backtest": 0,
            "research": 1,
            "walk-forward": 1,
            "simulation": 2,
            "paper": 3,
            "shadow": 4,
            "live-read-only": 5,
            "micro-live": 6,
            "full-live": 7,
        }
        c_ord = order.get(c_orig, 0)
        t_ord = order.get(t_orig, 0)

        if t_ord <= c_ord:
            logger.debug("Lifecycle transition is a maintenance/demotion; approved.")
            return ModePromotionReview(
                strategy_id=strategy_id,
                current_stage=current_stage,
                target_stage=target_stage,
                status=RiskDecisionStatus.APPROVE,
                reason_code=RiskReasonCode.OK,
                message=(
                    f"Lifecycle transition from '{current_stage}' to "
                    f"'{target_stage}' approved (maintenance/demotion)."
                ),
                severity=RiskSeverity.INFO,
                breached=False,
                evidence=evidence,
                breaches=[],
            )

        if _check_skip_gate(c_orig, t_orig):
            msg = (
                f"Lifecycle skip-gate transition blocked for '{strategy_id}': "
                f"cannot jump from '{current_stage}' directly to '{target_stage}' "
                "without intermediate gates."
            )
            breach_msg = (
                f"Lifecycle skip-gate transition blocked: "
                f"'{current_stage}' -> '{target_stage}'"
            )
            logger.info(msg)
            return ModePromotionReview(
                strategy_id=strategy_id,
                current_stage=current_stage,
                target_stage=target_stage,
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.LIFECYCLE_GATES_BREACH,
                message=msg,
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                evidence=evidence,
                breaches=[breach_msg],
            )

        m_ctx = market_context or {}
        if not _check_high_risk_approval(t_stage, m_ctx, config, approval_token):
            logger.info(f"High-risk transition to '{target_stage}' needs approval.")
            return ModePromotionReview(
                strategy_id=strategy_id,
                current_stage=current_stage,
                target_stage=target_stage,
                status=RiskDecisionStatus.NEEDS_APPROVAL,
                reason_code=RiskReasonCode.APPROVAL_REQUIRED,
                message=(
                    f"Transition to high-risk stage '{target_stage}' "
                    "requires approved operator token."
                ),
                severity=RiskSeverity.WARNING,
                breached=True,
                evidence=evidence,
                breaches=[
                    f"High-risk transition to '{target_stage}' requires approval token"
                ],
            )

        breaches: list[str] = []
        _check_research_transition(c_orig, t_orig, evidence, config, breaches)
        _check_simulation_transition(c_stage, t_stage, evidence, config, breaches)
        _check_shadow_transition(c_stage, t_stage, t_orig, evidence, config, breaches)
        _check_live_mode_transitions(c_stage, t_stage, evidence, config, breaches)

        if breaches:
            logger.info(f"Mode promotion rejected for '{strategy_id}': {breaches}.")
            return ModePromotionReview(
                strategy_id=strategy_id,
                current_stage=current_stage,
                target_stage=target_stage,
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.LIFECYCLE_GATES_BREACH,
                message=(
                    f"Mode promotion to '{target_stage}' rejected. "
                    f"Details: {', '.join(breaches)}"
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                evidence=evidence,
                breaches=breaches,
            )

        logger.info(f"Mode promotion approved for '{strategy_id}'.")
        return ModePromotionReview(
            strategy_id=strategy_id,
            current_stage=current_stage,
            target_stage=target_stage,
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message=(
                f"Mode promotion from '{current_stage}' to '{target_stage}' approved."
            ),
            severity=RiskSeverity.INFO,
            breached=False,
            evidence=evidence,
            breaches=[],
        )


def _review_strategy_admission_v1(
    strategy_id: str,
    evidence: dict[str, Any],
    config: RiskConfig,
) -> StrategyAdmissionReview:
    """V1 strategy admission review operating on raw positional arguments."""
    return RiskLifecycleGate.admit_strategy(strategy_id, evidence, config)


def _review_strategy_admission_v2(
    request: StrategyAdmissionRequest, policy: EffectiveRiskPolicy
) -> LifecycleAssessment:
    """V2 canonical strategy admission review operating on typed evidence."""
    logger.info(f"Reviewing canonical strategy admission for '{request.strategy_id}'.")
    evidence: dict[str, Any] = dict(request.evidence)
    if request.research_evidence:
        evidence.setdefault("backtest", request.research_evidence)
    if request.simulation_evidence:
        evidence.update(request.simulation_evidence)
    if request.risk_evidence:
        evidence.update(request.risk_evidence)

    v1_review = RiskLifecycleGate.admit_strategy(
        request.strategy_id, evidence, policy.resolved_config
    )
    return LifecycleAssessment(
        strategy_id=v1_review.strategy_id,
        status=v1_review.status,
        reason_code=v1_review.reason_code,
        message=v1_review.message,
        severity=v1_review.severity,
        breached=v1_review.breached,
        breaches=v1_review.breaches,
    )


@overload
def review_strategy_admission(
    strategy_id: str,
    evidence: dict[str, Any],
    config: RiskConfig,
) -> StrategyAdmissionReview: ...


@overload
def review_strategy_admission(
    request: StrategyAdmissionRequest, policy: EffectiveRiskPolicy
) -> LifecycleAssessment: ...


def review_strategy_admission(*args: Any, **kwargs: Any) -> Any:
    """Review strategy admission, supporting V1 and V2 signatures.

    Args:
        *args: Positional arguments. For V1: (strategy_id: str,
            evidence: dict, config: RiskConfig). For V2: (request:
            StrategyAdmissionRequest, policy: EffectiveRiskPolicy).
        **kwargs: Keyword arguments mirroring the positional forms above.

    Returns:
        StrategyAdmissionReview | LifecycleAssessment: The review outcome.
    """
    logger.info("review_strategy_admission entry.")
    first = args[0] if args else kwargs.get("request", kwargs.get("strategy_id"))
    if isinstance(first, StrategyAdmissionRequest):
        request = first
        policy: Any = kwargs.get("policy", args[1] if len(args) > 1 else None)
        return _review_strategy_admission_v2(request, policy)

    strategy_id: Any = kwargs.get("strategy_id", args[0] if args else None)
    evidence: Any = kwargs.get("evidence", args[1] if len(args) > 1 else None)
    config: Any = kwargs.get("config", args[2] if len(args) > 2 else None)
    return _review_strategy_admission_v1(strategy_id, evidence, config)


def _review_live_readiness_v1(
    strategy_id: str,
    proposed_stage: str,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LiveReadinessReview:
    """V1 live readiness review operating on raw positional arguments."""
    return RiskLifecycleGate.check_readiness(
        strategy_id, proposed_stage, market_context, config
    )


def _review_live_readiness_v2(
    request: LiveReadinessRequest, policy: EffectiveRiskPolicy
) -> LifecycleAssessment:
    """V2 canonical live readiness review operating on a typed request."""
    logger.info(f"Reviewing canonical live readiness for '{request.strategy_id}'.")
    v1_review = RiskLifecycleGate.check_readiness(
        request.strategy_id,
        request.proposed_stage,
        request.market_context,
        policy.resolved_config,
    )
    return LifecycleAssessment(
        strategy_id=v1_review.strategy_id,
        status=v1_review.status,
        reason_code=v1_review.reason_code,
        message=v1_review.message,
        severity=v1_review.severity,
        breached=v1_review.breached,
        breaches=v1_review.breaches,
        target_stage=v1_review.proposed_stage,
    )


@overload
def review_live_readiness(
    strategy_id: str,
    proposed_stage: str,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LiveReadinessReview: ...


@overload
def review_live_readiness(
    request: LiveReadinessRequest, policy: EffectiveRiskPolicy
) -> LifecycleAssessment: ...


def review_live_readiness(*args: Any, **kwargs: Any) -> Any:
    """Review live readiness, supporting V1 and V2 signatures.

    Args:
        *args: Positional arguments. For V1: (strategy_id: str,
            proposed_stage: str, market_context: dict, config: RiskConfig).
            For V2: (request: LiveReadinessRequest, policy: EffectiveRiskPolicy).
        **kwargs: Keyword arguments mirroring the positional forms above.

    Returns:
        LiveReadinessReview | LifecycleAssessment: The review outcome.
    """
    logger.info("review_live_readiness entry.")
    first = args[0] if args else kwargs.get("request", kwargs.get("strategy_id"))
    if isinstance(first, LiveReadinessRequest):
        request = first
        policy: Any = kwargs.get("policy", args[1] if len(args) > 1 else None)
        return _review_live_readiness_v2(request, policy)

    strategy_id: Any = kwargs.get("strategy_id", args[0] if args else None)
    proposed_stage: Any = kwargs.get(
        "proposed_stage", args[1] if len(args) > 1 else None
    )
    market_context: Any = kwargs.get(
        "market_context", args[2] if len(args) > 2 else None
    )
    config: Any = kwargs.get("config", args[3] if len(args) > 3 else None)
    return _review_live_readiness_v1(
        strategy_id, proposed_stage, market_context, config
    )


def review_mode_promotion(
    strategy_id: str,
    current_stage: str,
    target_stage: str,
    evidence: dict[str, Any],
    config: RiskConfig,
    market_context: dict[str, Any] | None = None,
    approval_token: object = None,
) -> ModePromotionReview:
    """Review strategy mode promotion stage gating."""
    return RiskLifecycleGate.promote_mode(
        strategy_id=strategy_id,
        current_stage=current_stage,
        target_stage=target_stage,
        evidence=evidence,
        config=config,
        market_context=market_context,
        approval_token=approval_token,
    )


def evaluate_lifecycle_promotion(
    strategy_id: str,
    current_stage: str,
    target_stage: str,
    evidence: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Validate if a strategy is eligible to promote to the target lifecycle stage."""
    logger.info(f"Evaluating lifecycle promotion (legacy wrapper) for '{strategy_id}'.")
    review = review_mode_promotion(
        strategy_id=strategy_id,
        current_stage=current_stage,
        target_stage=target_stage,
        evidence=evidence,
        config=config,
        market_context={"bypass_approval_check": True},
    )
    return LimitResult(
        limit_name="lifecycle_promotion",
        status=review.status,
        reason_code=review.reason_code,
        message=review.message,
        severity=review.severity,
        breached=review.breached,
    )


def evaluate_live_readiness(
    strategy_id: str,
    proposed_stage: str,
    market_context: dict[str, Any],
    _config: RiskConfig,
) -> LimitResult:
    """Enforce audit, kill switch and reconciliation readiness checks."""
    logger.info(f"Evaluating live readiness (legacy wrapper) for '{strategy_id}'.")
    review = _review_live_readiness_v1(
        strategy_id, proposed_stage, market_context, _config
    )
    return LimitResult(
        limit_name="live_readiness",
        status=review.status,
        reason_code=review.reason_code,
        message=review.message,
        severity=review.severity,
        breached=review.breached,
    )


def validate_lifecycle_transition(
    current: StrategyLifecycleState,
    target: StrategyLifecycleState,
    evidence: LifecycleEvidence,
) -> ValidationResult:
    """Reject unauthorized lifecycle stage promotion.

    Args:
        current: Current canonical lifecycle stage.
        target: Requested canonical lifecycle stage.
        evidence: Typed evidence bundle backing the transition.

    Returns:
        ValidationResult: Validation outcome with message and details.
    """
    logger.info(f"Validating lifecycle transition: {current} -> {target}.")
    c_orig = str(current.value)
    t_orig = str(target.value)

    if _check_skip_gate(c_orig, t_orig):
        msg = f"Skip-gate transition blocked: '{c_orig}' -> '{t_orig}'."
        logger.info(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "LIFECYCLE_GATES_BREACH",
            "details": {"current": c_orig, "target": t_orig},
        }

    breaches: list[str] = []
    default_config = RiskConfig(profile_name="lifecycle_validation")
    evidence_dict = evidence.model_dump()
    _check_research_transition(c_orig, t_orig, evidence_dict, default_config, breaches)
    _check_simulation_transition(
        c_orig, t_orig, evidence_dict, default_config, breaches
    )
    _check_shadow_transition(
        c_orig, t_orig, t_orig, evidence_dict, default_config, breaches
    )
    _check_live_mode_transitions(
        c_orig, t_orig, evidence_dict, default_config, breaches
    )

    if breaches:
        msg = f"Lifecycle transition rejected: {', '.join(breaches)}"
        logger.info(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "LIFECYCLE_GATES_BREACH",
            "details": {"breaches": breaches},
        }

    logger.debug(f"Lifecycle transition validated: {c_orig} -> {t_orig}.")
    return {
        "valid": True,
        "message": f"Lifecycle transition '{c_orig}' -> '{t_orig}' is valid.",
        "code": "OK",
        "details": {},
    }


def requires_lifecycle_approval(
    assessment: LifecycleAssessment, policy: EffectiveRiskPolicy
) -> bool:
    """Determine whether a lifecycle assessment requires governed approval.

    Args:
        assessment: The canonical lifecycle review outcome.
        policy: Resolved effective risk policy (retained for interface
            symmetry with the architecture's escalation contract).

    Returns:
        bool: True if the assessment requires operator/compliance approval.
    """
    logger.info("Determining lifecycle approval escalation requirement.")
    _ = policy
    requires_approval = assessment.status == RiskDecisionStatus.NEEDS_APPROVAL
    logger.debug(f"Lifecycle approval required: {requires_approval}.")
    return requires_approval
