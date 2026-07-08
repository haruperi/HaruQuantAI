"""Single-purpose pure limit evaluators.

Evaluates kill-switch, evidence-freshness, loss, exposure, tail-risk, margin,
session, execution, and frequency limits from supplied canonical evidence.
Every function here is pure: given the same evidence and policy, it always
returns the same :class:`~app.services.risk.limits.contracts.LimitResult`.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.risk.limits.contracts import LimitResult
from app.services.risk.models import (
    KillSwitchStateEnum,
    ProposedTrade,
    RiskAssessmentRequest,
    RiskConfig,
    RiskDecisionStatus,
    RiskMode,
    RiskReasonCode,
    RiskSeverity,
)
from app.utils.logger import logger
from app.utils.normalization import to_utc_datetime, utc_now

if TYPE_CHECKING:
    from datetime import datetime

    from app.services.risk.models import (
        ExecutionRiskSnapshot,
        ExpectedShortfallSnapshot,
        PortfolioRiskSnapshot,
        VaRSnapshot,
    )
    from app.services.risk.policy.contracts import EffectiveRiskPolicy
    from app.services.risk.stress.contracts import StressSummary


def _is_live_sensitive(request: RiskAssessmentRequest) -> bool:
    """Check if request environment or mode is live-sensitive.

    Args:
        request: The active risk assessment request.

    Returns:
        bool: True if the request targets a live-sensitive mode/environment.
    """
    mode = request.market_context.get("mode")
    env = request.market_context.get("environment")
    if mode in {
        RiskMode.MICRO_LIVE,
        RiskMode.FULL_LIVE,
        "micro_live",
        "full_live",
    }:
        return True
    return env in {"production", "live"}


def check_kill_switch_state(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if the global, portfolio, or strategy kill switch is active.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: BLOCK if any relevant kill switch is active, else APPROVE.
    """
    from app.services.risk.kill_switch import get_kill_switch_manager

    manager = get_kill_switch_manager()
    is_live = request.market_context.get("mode") in {
        "micro_live",
        "full_live",
    } or request.market_context.get("environment") in {"production", "live"}

    if request.market_context.get("kill_switch_active", False):
        logger.info("Global kill switch is active (context override).")
        return LimitResult(
            limit_name="kill_switch_state",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
            message="Global kill switch is active.",
            severity=RiskSeverity.EMERGENCY_HALT,
            breached=True,
        )

    if manager.is_blocked("global", "*", is_live=is_live) or manager.is_blocked(
        "portfolio", "*", is_live=is_live
    ):
        logger.info("Global or portfolio kill switch is active.")
        return LimitResult(
            limit_name="kill_switch_state",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
            message="Global or portfolio kill switch is active.",
            severity=RiskSeverity.EMERGENCY_HALT,
            breached=True,
        )

    action = request.proposed_action
    if action:
        strategy_id = getattr(action, "strategy_id", None)
        if strategy_id and manager.is_blocked(
            "strategy", str(strategy_id), is_live=is_live
        ):
            logger.info(f"Kill switch is active for strategy '{strategy_id}'.")
            return LimitResult(
                limit_name="kill_switch_state",
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
                message=f"Kill switch is active for strategy '{strategy_id}'.",
                severity=RiskSeverity.EMERGENCY_HALT,
                breached=True,
            )

        allocations = getattr(action, "allocations", None)
        if isinstance(allocations, dict):
            for strat_id in allocations:
                if manager.is_blocked("strategy", str(strat_id), is_live=is_live):
                    logger.info(f"Kill switch is active for strategy '{strat_id}'.")
                    return LimitResult(
                        limit_name="kill_switch_state",
                        status=RiskDecisionStatus.BLOCK,
                        reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
                        message=f"Kill switch is active for strategy '{strat_id}'.",
                        severity=RiskSeverity.EMERGENCY_HALT,
                        breached=True,
                    )

        symbol = getattr(action, "symbol", None)
        if symbol and manager.is_blocked("symbol", str(symbol), is_live=is_live):
            logger.info(f"Kill switch is active for symbol '{symbol}'.")
            return LimitResult(
                limit_name="kill_switch_state",
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
                message=(
                    f"Kill switch is active for symbol '{symbol}' or its currency legs."
                ),
                severity=RiskSeverity.EMERGENCY_HALT,
                breached=True,
            )

    logger.debug("Kill switch is inactive.")
    return LimitResult(
        limit_name="kill_switch_state",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Kill switch is inactive.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_stale_evidence_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if input snapshots are stale or missing required live parameters.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: APPROVE/NEEDS_MORE_EVIDENCE/REJECT/BLOCK based on freshness.
    """
    now = utc_now()
    stale_limit = float(request.market_context.get("max_stale_seconds", 60.0))

    freshness = request.market_context.get("freshness")
    if freshness is None:
        if _is_live_sensitive(request):
            logger.info("Live mode blocked: missing freshness metadata.")
            return LimitResult(
                limit_name="stale_evidence",
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.STALE_EVIDENCE,
                message="Live mode blocked: missing freshness metadata.",
                severity=RiskSeverity.CRITICAL_BREACH,
                breached=True,
            )
        logger.debug("Missing freshness metadata (non-live).")
        return LimitResult(
            limit_name="stale_evidence",
            status=RiskDecisionStatus.NEEDS_MORE_EVIDENCE,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message="Missing freshness metadata.",
            severity=RiskSeverity.WARNING,
            breached=True,
        )

    fresh_dt = to_utc_datetime(freshness)
    age = (now - fresh_dt).total_seconds()
    if not math.isfinite(age) or not math.isfinite(stale_limit):
        logger.error("Freshness calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="stale_evidence",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Freshness calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if age > stale_limit:
        status = (
            RiskDecisionStatus.BLOCK
            if _is_live_sensitive(request)
            else RiskDecisionStatus.REJECT
        )
        logger.info(f"Evidence is stale by {age:.1f}s (max allowed: {stale_limit}s).")
        return LimitResult(
            limit_name="stale_evidence",
            status=status,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=(f"Evidence is stale by {age:.1f}s (max allowed: {stale_limit}s)."),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"age_seconds": age},
        )

    logger.debug(f"Evidence freshness is within safe limits (age={age:.1f}s).")
    return LimitResult(
        limit_name="stale_evidence",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Evidence freshness is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_max_drawdown_limit(
    request: RiskAssessmentRequest, config: RiskConfig
) -> LimitResult:
    """Check if total drawdown exceeds soft or hard limit ceilings.

    Args:
        request: The active risk assessment request.
        config: Active risk configuration.

    Returns:
        LimitResult: BLOCK on hard breach, APPROVE (with warning) on soft
            breach, or APPROVE otherwise.
    """
    drawdown = request.market_context.get("drawdown")
    if drawdown is None:
        balance = request.portfolio_state.balance
        equity = request.portfolio_state.equity
        drawdown = (
            max(Decimal(0), (balance - equity) / balance) if balance > 0 else Decimal(0)
        )

    drawdown = Decimal(str(drawdown))
    if (
        not math.isfinite(float(drawdown))
        or not math.isfinite(float(config.max_total_loss_pct))
        or not math.isfinite(float(config.max_total_loss_pct_advisory))
    ):
        logger.error("Drawdown calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Drawdown calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if drawdown > config.max_total_loss_pct:
        logger.info(f"Hard total drawdown limit breached: {drawdown:.2%}.")
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.DRAWDOWN_BREACH,
            message=(
                f"Hard total drawdown limit breached: {drawdown:.2%} > "
                f"{config.max_total_loss_pct:.2%}."
            ),
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
            details={"drawdown": float(drawdown)},
        )

    if drawdown > config.max_total_loss_pct_advisory:
        logger.info(f"Advisory drawdown limit warning: {drawdown:.2%}.")
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message=(
                f"Advisory drawdown limit warning: {drawdown:.2%} > "
                f"{config.max_total_loss_pct_advisory:.2%}."
            ),
            severity=RiskSeverity.WARNING,
            breached=True,
            details={"drawdown": float(drawdown)},
        )

    logger.debug(f"Total drawdown is within safe ceilings: {drawdown:.2%}.")
    return LimitResult(
        limit_name="max_drawdown_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Total drawdown is within safe ceilings.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_daily_loss_limit(
    request: RiskAssessmentRequest, config: RiskConfig
) -> LimitResult:
    """Check if realized and floating daily loss exceeds the profile limits.

    Args:
        request: The active risk assessment request.
        config: Active risk configuration.

    Returns:
        LimitResult: BLOCK/REJECT on breach, NEEDS_MORE_EVIDENCE if missing
            in non-live modes, else APPROVE.
    """
    daily_loss_pct = request.market_context.get("daily_loss_pct")
    if daily_loss_pct is None:
        if _is_live_sensitive(request):
            logger.info("Live mode blocked: missing daily loss metrics.")
            return LimitResult(
                limit_name="daily_loss_limit",
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.STALE_EVIDENCE,
                message="Live mode blocked: missing daily loss metrics.",
                severity=RiskSeverity.CRITICAL_BREACH,
                breached=True,
            )
        logger.debug("Missing daily loss metrics (non-live).")
        return LimitResult(
            limit_name="daily_loss_limit",
            status=RiskDecisionStatus.NEEDS_MORE_EVIDENCE,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message="Missing daily loss metrics.",
            severity=RiskSeverity.WARNING,
            breached=True,
        )

    daily_loss_pct = Decimal(str(daily_loss_pct))
    if not math.isfinite(float(daily_loss_pct)) or not math.isfinite(
        float(config.max_daily_loss_pct)
    ):
        logger.error("Daily loss calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="daily_loss_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Daily loss calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if daily_loss_pct >= config.max_daily_loss_pct:
        status = (
            RiskDecisionStatus.BLOCK
            if _is_live_sensitive(request)
            else RiskDecisionStatus.REJECT
        )
        logger.info(f"Daily loss limit breached: {daily_loss_pct:.2%}.")
        return LimitResult(
            limit_name="daily_loss_limit",
            status=status,
            reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
            message=(
                f"Daily loss limit breached: {daily_loss_pct:.2%} >= "
                f"{config.max_daily_loss_pct:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"daily_loss_pct": float(daily_loss_pct)},
        )

    logger.debug(f"Daily loss is within safe limits: {daily_loss_pct:.2%}.")
    return LimitResult(
        limit_name="daily_loss_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Daily loss is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_strategy_loss_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if a specific strategy drawdown limit is exceeded.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; the strategy-level limit
            is sourced from market_context to allow per-request overrides).

    Returns:
        LimitResult: REJECT on breach, APPROVE otherwise.
    """
    strat_loss_pct = request.market_context.get("strategy_loss_pct")
    strat_limit = Decimal(
        str(request.market_context.get("max_strategy_loss_pct", "0.04"))
    )

    if strat_loss_pct is None:
        logger.debug("No strategy loss details provided; check skipped.")
        return LimitResult(
            limit_name="strategy_loss_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No strategy loss details provided. Skipping.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    strat_loss_pct = Decimal(str(strat_loss_pct))
    if not math.isfinite(float(strat_loss_pct)) or not math.isfinite(
        float(strat_limit)
    ):
        logger.error("Strategy loss calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="strategy_loss_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Strategy loss calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if strat_loss_pct >= strat_limit:
        logger.info(f"Strategy loss limit breached: {strat_loss_pct:.2%}.")
        return LimitResult(
            limit_name="strategy_loss_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
            message=(
                f"Strategy loss limit breached: {strat_loss_pct:.2%} >= "
                f"{strat_limit:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"strategy_loss_pct": float(strat_loss_pct)},
        )

    logger.debug(f"Strategy loss is within safe limits: {strat_loss_pct:.2%}.")
    return LimitResult(
        limit_name="strategy_loss_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Strategy loss is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_news_blackout(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if news blackout window is active for the target symbols.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: REJECT if blackout is active, else APPROVE.
    """
    is_blackout = request.market_context.get("news_blackout_active", False)
    if is_blackout:
        logger.info("High impact news blackout window is active.")
        return LimitResult(
            limit_name="news_blackout",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.NEWS_BLACKOUT,
            message="High impact news blackout window is active.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    logger.debug("Outside of news blackout windows.")
    return LimitResult(
        limit_name="news_blackout",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Outside of news blackout windows.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_rollover_blackout(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if broker midnight rollover blackout window is active.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: REJECT if blackout is active, else APPROVE.
    """
    is_blackout = request.market_context.get("rollover_blackout_active", False)
    if is_blackout:
        logger.info("Rollover blackout window surrounding broker midnight is active.")
        return LimitResult(
            limit_name="rollover_blackout",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.ROLLOVER_BLACKOUT,
            message=("Rollover blackout window surrounding broker midnight is active."),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    logger.debug("Outside of rollover blackout windows.")
    return LimitResult(
        limit_name="rollover_blackout",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Outside of rollover blackout windows.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_spread_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if current market spread exceeds the maximum allowed.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: REJECT on breach, APPROVE otherwise.
    """
    spread = request.market_context.get("spread")
    max_spread = Decimal(str(request.market_context.get("max_spread", "0.0050")))

    if spread is None:
        logger.debug("No spread provided; check skipped.")
        return LimitResult(
            limit_name="spread_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No spread provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    spread = Decimal(str(spread))
    if not math.isfinite(float(spread)) or not math.isfinite(float(max_spread)):
        logger.error("Spread calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="spread_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Spread calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if spread > max_spread:
        logger.info(f"Spread limit breached: {spread} > {max_spread}.")
        return LimitResult(
            limit_name="spread_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.SPREAD_BREACH,
            message=f"Spread limit breached: {spread} > {max_spread}.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"spread": float(spread)},
        )

    logger.debug(f"Spread is within safe limits: {spread}.")
    return LimitResult(
        limit_name="spread_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Spread is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_slippage_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if current estimated execution slippage is within bounds.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: REJECT on breach, APPROVE otherwise.
    """
    slippage = request.market_context.get("slippage")
    max_slippage = Decimal(str(request.market_context.get("max_slippage", "0.0020")))

    if slippage is None:
        logger.debug("No slippage provided; check skipped.")
        return LimitResult(
            limit_name="slippage_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No slippage provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    slippage = Decimal(str(slippage))
    if not math.isfinite(float(slippage)) or not math.isfinite(float(max_slippage)):
        logger.error("Slippage calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="slippage_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Slippage calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if slippage > max_slippage:
        logger.info(f"Slippage limit breached: {slippage} > {max_slippage}.")
        return LimitResult(
            limit_name="slippage_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.SLIPPAGE_BREACH,
            message=f"Slippage limit breached: {slippage} > {max_slippage}.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"slippage": float(slippage)},
        )

    logger.debug(f"Slippage is within safe limits: {slippage}.")
    return LimitResult(
        limit_name="slippage_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Slippage is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_trade_frequency_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if short-term trade frequency limits are exceeded.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: REJECT/BLOCK on breach or invalid input, else APPROVE.
    """
    freq = request.market_context.get("trade_frequency")
    max_freq = int(request.market_context.get("max_trade_frequency", 10))

    if freq is None:
        logger.debug("No trade frequency data provided; check skipped.")
        return LimitResult(
            limit_name="trade_frequency_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No trade frequency data provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    try:
        freq_f = float(freq)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid trade frequency input: {e}")
        return LimitResult(
            limit_name="trade_frequency_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=f"Invalid trade frequency input: {e}",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if not math.isfinite(float(freq_f)) or not math.isfinite(float(max_freq)):
        logger.error("Trade frequency calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="trade_frequency_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Trade frequency calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if int(freq) > max_freq:
        logger.info(f"Trade frequency limit breached: {freq} > {max_freq}.")
        return LimitResult(
            limit_name="trade_frequency_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.FREQUENCY_BREACH,
            message=(
                f"Trade frequency limit breached: {freq} > {max_freq} per minute."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"trade_frequency": int(freq)},
        )

    logger.debug(f"Trade frequency is within safe limits: {freq}.")
    return LimitResult(
        limit_name="trade_frequency_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Trade frequency is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_pending_order_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if the count of open pending orders exceeds the configured capacity.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: REJECT/BLOCK on breach or invalid input, else APPROVE.
    """
    pending_count = request.market_context.get("pending_orders_count")
    max_pending = int(request.market_context.get("max_pending_orders", 5))

    if pending_count is None:
        logger.debug("No pending order count provided; check skipped.")
        return LimitResult(
            limit_name="pending_order_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No pending order count provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    try:
        pending_f = float(pending_count)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid pending orders count input: {e}")
        return LimitResult(
            limit_name="pending_order_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=f"Invalid pending orders count input: {e}",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if not math.isfinite(float(pending_f)) or not math.isfinite(float(max_pending)):
        logger.error("Pending orders count calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="pending_order_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Pending orders count calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    if int(pending_count) > max_pending:
        logger.info(f"Pending order limit breached: {pending_count} > {max_pending}.")
        return LimitResult(
            limit_name="pending_order_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.FREQUENCY_BREACH,
            message=(f"Pending order limit breached: {pending_count} > {max_pending}."),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"pending_orders_count": int(pending_count)},
        )

    logger.debug(f"Pending order count is within safe limits: {pending_count}.")
    return LimitResult(
        limit_name="pending_order_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Pending order count is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_portfolio_exposure_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if portfolio gross exposure exceeds total capital limits.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: BLOCK/REJECT on breach or invalid state, else APPROVE.
    """
    gross_exposure = Decimal(
        str(request.market_context.get("portfolio_gross_exposure", "0.0"))
    )
    equity = request.portfolio_state.equity
    max_portfolio_exposure = Decimal(
        str(request.market_context.get("max_portfolio_exposure", "5.0"))
    )

    proposed_exposure = Decimal(0)
    if isinstance(request.proposed_action, ProposedTrade):
        proposed_exposure = request.proposed_action.volume * Decimal(
            str(request.market_context.get("contract_size", 100000))
        )

    total_exposure = gross_exposure + proposed_exposure
    if equity <= 0:
        logger.error("Portfolio exposure check failed: equity is zero/negative.")
        return LimitResult(
            limit_name="portfolio_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.CONCENTRATION_BREACH,
            message="Exposure check failed: portfolio equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if (
        not math.isfinite(float(total_exposure))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_portfolio_exposure))
    ):
        logger.error("Portfolio exposure calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="portfolio_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Portfolio exposure calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    ratio = total_exposure / equity
    if ratio > max_portfolio_exposure:
        logger.info(f"Portfolio exposure limit breached: {ratio:.2f}x.")
        return LimitResult(
            limit_name="portfolio_exposure_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.CONCENTRATION_BREACH,
            message=(
                f"Portfolio exposure limit breached: {ratio:.2f}x > "
                f"{max_portfolio_exposure:.2f}x."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"exposure_ratio": float(ratio)},
        )

    logger.debug(f"Portfolio exposure is within safe capacity: {ratio:.2f}x.")
    return LimitResult(
        limit_name="portfolio_exposure_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Portfolio exposure is within safe capacity.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_symbol_exposure_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if single symbol gross exposure exceeds concentration limits.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: BLOCK/REJECT on breach or invalid state, else APPROVE.
    """
    symbol = ""
    if isinstance(request.proposed_action, ProposedTrade):
        symbol = request.proposed_action.symbol

    if not symbol:
        logger.debug("No symbol exposure check required.")
        return LimitResult(
            limit_name="symbol_exposure_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No symbol exposure check required.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    symbol_exposure = Decimal(
        str(request.market_context.get(f"symbol_exposure_{symbol}", "0.0"))
    )
    equity = request.portfolio_state.equity
    max_symbol_exposure = Decimal(
        str(request.market_context.get("max_symbol_exposure", "1.0"))
    )

    proposed_exposure = Decimal(0)
    if isinstance(request.proposed_action, ProposedTrade):
        proposed_exposure = request.proposed_action.volume * Decimal(
            str(request.market_context.get("contract_size", 100000))
        )

    total_exposure = symbol_exposure + proposed_exposure
    if equity <= 0:
        logger.error("Symbol exposure check failed: equity is zero/negative.")
        return LimitResult(
            limit_name="symbol_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.CONCENTRATION_BREACH,
            message="Symbol exposure check failed: equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if (
        not math.isfinite(float(total_exposure))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_symbol_exposure))
    ):
        logger.error("Symbol exposure calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="symbol_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Symbol exposure calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    ratio = total_exposure / equity
    if ratio > max_symbol_exposure:
        logger.info(f"Symbol {symbol} exposure limit breached: {ratio:.2f}x.")
        return LimitResult(
            limit_name="symbol_exposure_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.CONCENTRATION_BREACH,
            message=(
                f"Symbol {symbol} exposure limit breached: {ratio:.2f}x > "
                f"{max_symbol_exposure:.2f}x."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"symbol": symbol, "exposure_ratio": float(ratio)},
        )

    logger.debug(f"Symbol {symbol} exposure is within concentration ceilings.")
    return LimitResult(
        limit_name="symbol_exposure_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message=f"Symbol {symbol} exposure is within concentration ceilings.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_currency_exposure_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if target currency gross exposure exceeds concentration ceilings.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: BLOCK/REJECT on breach or invalid state, else APPROVE.
    """
    gross_ccy_exposure = Decimal(
        str(request.market_context.get("currency_gross_exposure", "0.0"))
    )
    equity = request.portfolio_state.equity
    max_ccy_exposure = Decimal(
        str(request.market_context.get("max_currency_exposure", "1.5"))
    )

    if equity <= 0:
        logger.error("Currency exposure check failed: equity is zero/negative.")
        return LimitResult(
            limit_name="currency_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.CURRENCY_BREACH,
            message="Currency exposure check failed: equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if (
        not math.isfinite(float(gross_ccy_exposure))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_ccy_exposure))
    ):
        logger.error("Currency exposure calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="currency_exposure_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Currency exposure calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    ratio = gross_ccy_exposure / equity
    if ratio > max_ccy_exposure:
        logger.info(f"Currency exposure limit breached: {ratio:.2f}x.")
        return LimitResult(
            limit_name="currency_exposure_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.CURRENCY_BREACH,
            message=(
                f"Currency exposure limit breached: {ratio:.2f}x > "
                f"{max_ccy_exposure:.2f}x."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"exposure_ratio": float(ratio)},
        )

    logger.debug(f"Currency exposure is within concentration limits: {ratio:.2f}x.")
    return LimitResult(
        limit_name="currency_exposure_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Currency exposure is within concentration limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_correlation_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if cluster exposure or correlation exceeds limits.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration providing the base correlation
            threshold.

    Returns:
        LimitResult: BLOCK/REJECT on breach or invalid state, else APPROVE.
    """
    portfolio_corr = Decimal(
        str(request.market_context.get("portfolio_correlation", "0.0"))
    )
    max_corr = _config.correlation_threshold
    reject_thresh = min(
        Decimal("0.95"),
        max(Decimal("0.80"), max_corr * Decimal("1.5")),
    )

    if not math.isfinite(float(portfolio_corr)) or not math.isfinite(float(max_corr)):
        logger.error("Correlation calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="correlation_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Correlation calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if abs(portfolio_corr) >= reject_thresh:
        logger.info(f"Individual correlation {portfolio_corr:.2f} exceeds ceiling.")
        return LimitResult(
            limit_name="correlation_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.CORRELATION_BREACH,
            message=(
                f"Proposed trade individual correlation {portfolio_corr:.2f} exceeds "
                f"hard rejection ceiling of {reject_thresh:.2f}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"marginal_correlation": float(portfolio_corr)},
        )

    cluster_exposure = Decimal(
        str(request.market_context.get("correlated_cluster_exposure", "0.0"))
    )
    equity = request.portfolio_state.equity
    max_cluster_exposure = Decimal(
        str(request.market_context.get("max_correlated_exposure", "2.0"))
    )

    if equity <= 0:
        logger.error("Cluster check failed: portfolio equity is zero/negative.")
        return LimitResult(
            limit_name="correlated_cluster_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.CORRELATION_BREACH,
            message="Cluster check failed: portfolio equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if (
        not math.isfinite(float(cluster_exposure))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_cluster_exposure))
    ):
        logger.error("Correlation exposure calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="correlated_cluster_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Correlation exposure calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )
    ratio = cluster_exposure / equity
    if ratio > max_cluster_exposure:
        logger.info(f"Correlated cluster exposure limit breached: {ratio:.2f}x.")
        return LimitResult(
            limit_name="correlated_cluster_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.CORRELATION_BREACH,
            message=(
                f"Correlated cluster exposure limit breached: {ratio:.2f}x > "
                f"{max_cluster_exposure:.2f}x."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"exposure_ratio": float(ratio)},
        )

    logger.debug("Correlated cluster and individual correlation are within limits.")
    return LimitResult(
        limit_name="correlated_cluster_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Correlated cluster and individual correlation are within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_var_limit(request: RiskAssessmentRequest, _config: RiskConfig) -> LimitResult:
    """Check if portfolio Value-at-Risk exceeds configuration ceilings.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: BLOCK/REJECT on breach or invalid state, else APPROVE.
    """
    var_val = request.market_context.get("var_metric")
    equity = request.portfolio_state.equity
    max_var_ratio = Decimal(str(request.market_context.get("max_var_ratio", "0.05")))

    if var_val is None:
        logger.debug("No Value-at-Risk metric provided; check skipped.")
        return LimitResult(
            limit_name="var_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No Value-at-Risk metric provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    var_val = Decimal(str(var_val))
    if (
        not math.isfinite(float(var_val))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_var_ratio))
    ):
        logger.error("VaR calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="var_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="VaR calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if equity <= 0:
        logger.error("VaR check failed: portfolio equity is zero/negative.")
        return LimitResult(
            limit_name="var_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.VAR_BREACH,
            message="VaR check failed: portfolio equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    ratio = var_val / equity
    if ratio > max_var_ratio:
        logger.info(f"Value-at-Risk limit breached: {ratio:.2%}.")
        return LimitResult(
            limit_name="var_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.VAR_BREACH,
            message=f"Value-at-Risk limit breached: {ratio:.2%} > {max_var_ratio:.2%}.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"var_ratio": float(ratio)},
        )

    logger.debug(f"Value-at-Risk is within safe bounds: {ratio:.2%}.")
    return LimitResult(
        limit_name="var_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Value-at-Risk is within safe bounds.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_expected_shortfall_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if portfolio Expected Shortfall exceeds tail risk ceilings.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: BLOCK/REJECT on breach or invalid state, else APPROVE.
    """
    es_val = request.market_context.get("es_metric")
    equity = request.portfolio_state.equity
    max_es_ratio = Decimal(str(request.market_context.get("max_es_ratio", "0.08")))

    if es_val is None:
        logger.debug("No Expected Shortfall metric provided; check skipped.")
        return LimitResult(
            limit_name="expected_shortfall_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No Expected Shortfall metric provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    es_val = Decimal(str(es_val))
    if (
        not math.isfinite(float(es_val))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_es_ratio))
    ):
        logger.error("Expected Shortfall calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="expected_shortfall_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Expected Shortfall calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if equity <= 0:
        logger.error("ES check failed: portfolio equity is zero or negative.")
        return LimitResult(
            limit_name="expected_shortfall_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.ES_BREACH,
            message="ES check failed: portfolio equity is zero or negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    ratio = es_val / equity
    if ratio > max_es_ratio:
        logger.info(f"Expected Shortfall limit breached: {ratio:.2%}.")
        return LimitResult(
            limit_name="expected_shortfall_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.ES_BREACH,
            message=(
                f"Expected Shortfall limit breached: {ratio:.2%} > {max_es_ratio:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"es_ratio": float(ratio)},
        )

    logger.debug(f"Expected Shortfall is within safe bounds: {ratio:.2%}.")
    return LimitResult(
        limit_name="expected_shortfall_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Expected Shortfall is within safe bounds.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_stress_loss_limit(
    request: RiskAssessmentRequest, _config: RiskConfig
) -> LimitResult:
    """Check if maximum projected shock stress loss exceeds limits.

    Args:
        request: The active risk assessment request.
        _config: Active risk configuration (unused; kept for the uniform
            evaluator signature).

    Returns:
        LimitResult: BLOCK/REJECT on breach or invalid state, else APPROVE.
    """
    stress_val = request.market_context.get("stress_loss_val")
    equity = request.portfolio_state.equity
    max_stress_ratio = Decimal(
        str(request.market_context.get("max_stress_ratio", "0.15"))
    )

    if stress_val is None:
        logger.debug("No stress scenario loss provided; check skipped.")
        return LimitResult(
            limit_name="stress_loss_limit",
            status=RiskDecisionStatus.APPROVE,
            reason_code=RiskReasonCode.OK,
            message="No stress scenario loss provided.",
            severity=RiskSeverity.INFO,
            breached=False,
        )

    stress_val = Decimal(str(stress_val))
    if (
        not math.isfinite(float(stress_val))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(max_stress_ratio))
    ):
        logger.error("Stress loss calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="stress_loss_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Stress loss calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if equity <= 0:
        logger.error("Stress check failed: portfolio equity is zero/negative.")
        return LimitResult(
            limit_name="stress_loss_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.STRESS_BREACH,
            message="Stress check failed: portfolio equity is zero/negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    ratio = stress_val / equity
    if ratio > max_stress_ratio:
        logger.info(f"Stress loss limit breached: {ratio:.2%}.")
        return LimitResult(
            limit_name="stress_loss_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STRESS_BREACH,
            message=(
                f"Stress loss limit breached: {ratio:.2%} > {max_stress_ratio:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"stress_ratio": float(ratio)},
        )

    logger.debug(f"Max projected stress loss is within survival capacity: {ratio:.2%}.")
    return LimitResult(
        limit_name="stress_loss_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Max projected stress loss is within survival capacity.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_leverage_limit(
    request: RiskAssessmentRequest, config: RiskConfig
) -> LimitResult:
    """Check if effective leverage is below target settings.

    Args:
        request: The active risk assessment request.
        config: Active risk configuration.

    Returns:
        LimitResult: BLOCK/REJECT on breach or invalid state, else APPROVE.
    """
    leverage = request.market_context.get("effective_leverage")
    if leverage is None:
        gross = Decimal(
            str(request.market_context.get("portfolio_gross_exposure", "0.0"))
        )
        equity = request.portfolio_state.equity
        leverage = gross / equity if equity > 0 else Decimal(0)

    leverage = Decimal(str(leverage))
    if not math.isfinite(float(leverage)) or not math.isfinite(
        float(config.max_effective_leverage)
    ):
        logger.error("Leverage calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="leverage_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Leverage calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if leverage > config.max_effective_leverage:
        logger.info(f"Leverage limit breached: {leverage:.1f}x.")
        return LimitResult(
            limit_name="leverage_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.LEVERAGE_BREACH,
            message=(
                f"Leverage limit breached: {leverage:.1f}x > "
                f"{config.max_effective_leverage:.1f}x."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"leverage": float(leverage)},
        )

    logger.debug(f"Effective leverage is within safe capacity: {leverage:.1f}x.")
    return LimitResult(
        limit_name="leverage_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Effective leverage is within safe capacity.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_margin_limit(
    request: RiskAssessmentRequest, config: RiskConfig
) -> LimitResult:
    """Check if margin utilization is below target settings.

    Args:
        request: The active risk assessment request.
        config: Active risk configuration.

    Returns:
        LimitResult: BLOCK/REJECT on breach or invalid state, else APPROVE.
    """
    margin_used = request.portfolio_state.margin_used
    equity = request.portfolio_state.equity

    if equity <= 0:
        logger.error("Margin check failed: portfolio equity is zero or negative.")
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.MARGIN_BREACH,
            message="Margin check failed: portfolio equity is zero or negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    ratio = margin_used / equity
    if (
        not math.isfinite(float(ratio))
        or not math.isfinite(float(equity))
        or not math.isfinite(float(margin_used))
        or not math.isfinite(float(config.max_margin_utilization_pct))
    ):
        logger.error("Margin calculation resolved to non-finite value.")
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.UNEXPECTED_ERROR,
            message="Margin calculation resolved to non-finite value.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    if ratio > config.max_margin_utilization_pct:
        logger.info(f"Margin utilization limit breached: {ratio:.2%}.")
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.MARGIN_BREACH,
            message=(
                f"Margin utilization limit breached: {ratio:.2%} > "
                f"{config.max_margin_utilization_pct:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"margin_utilization": float(ratio)},
        )

    logger.debug(f"Margin utilization is within safe ceilings: {ratio:.2%}.")
    return LimitResult(
        limit_name="margin_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Margin utilization is within safe ceilings.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_kill_switch(state: KillSwitchStateEnum) -> LimitResult:
    """Block when a kill-switch state is active or indeterminate.

    Args:
        state: The current kill-switch state enum value.

    Returns:
        LimitResult: BLOCK when active/locked/unknown, else APPROVE.
    """
    logger.info(f"Checking canonical kill-switch state: {state}.")
    if state in {
        KillSwitchStateEnum.ACTIVE,
        KillSwitchStateEnum.LOCKED,
        KillSwitchStateEnum.TRIGGERED,
        KillSwitchStateEnum.UNKNOWN,
    }:
        logger.info(f"Kill switch check blocked for state '{state}'.")
        return LimitResult(
            limit_name="kill_switch_state",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.KILL_SWITCH_ACTIVE,
            message=f"Kill switch state '{state}' blocks trading.",
            severity=RiskSeverity.EMERGENCY_HALT,
            breached=True,
            details={"state": str(state)},
        )

    logger.debug(f"Kill switch state '{state}' permits trading.")
    return LimitResult(
        limit_name="kill_switch_state",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message=f"Kill switch state '{state}' permits trading.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_evidence_freshness(
    request: RiskAssessmentRequest,
    policy: EffectiveRiskPolicy,
    now_utc: datetime,
) -> LimitResult:
    """Block stale or incomplete mandatory evidence using a resolved policy.

    Args:
        request: The active risk assessment request.
        policy: Resolved effective risk policy providing the staleness cap.
        now_utc: Current UTC timestamp used to compute evidence age.

    Returns:
        LimitResult: BLOCK/REJECT on stale evidence, else APPROVE.
    """
    logger.info("Checking canonical evidence freshness against resolved policy.")
    stale_limit = float(
        request.market_context.get("max_stale_seconds")
        or policy.resolved_config.experimental_features.get("max_stale_seconds")
        or 60.0
    )
    freshness = request.freshness
    if freshness is None:
        logger.info("Evidence freshness timestamp missing.")
        return LimitResult(
            limit_name="stale_evidence",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message="Missing evidence freshness timestamp.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
        )

    age = (now_utc - to_utc_datetime(freshness)).total_seconds()
    if age > stale_limit:
        logger.info(f"Canonical evidence is stale by {age:.1f}s.")
        return LimitResult(
            limit_name="stale_evidence",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STALE_EVIDENCE,
            message=f"Evidence is stale by {age:.1f}s (max allowed: {stale_limit}s).",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"age_seconds": age},
        )

    logger.debug(f"Canonical evidence freshness is within bounds (age={age:.1f}s).")
    return LimitResult(
        limit_name="stale_evidence",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Evidence freshness is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_daily_loss(
    snapshot: PortfolioRiskSnapshot, policy: EffectiveRiskPolicy
) -> LimitResult:
    """Evaluate a portfolio snapshot's daily-loss budget against policy.

    Args:
        snapshot: Canonical portfolio-level risk snapshot.
        policy: Resolved effective risk policy providing the daily-loss cap.

    Returns:
        LimitResult: BLOCK on breach, APPROVE otherwise.
    """
    logger.info("Checking canonical daily loss budget.")
    limit = policy.resolved_config.max_daily_loss_pct
    if snapshot.drawdown >= limit:
        logger.info(f"Canonical daily loss limit breached: {snapshot.drawdown:.2%}.")
        return LimitResult(
            limit_name="daily_loss_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
            message=(
                f"Daily loss budget breached: {snapshot.drawdown:.2%} >= {limit:.2%}."
            ),
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
            details={"drawdown": float(snapshot.drawdown)},
        )

    logger.debug(f"Canonical daily loss is within budget: {snapshot.drawdown:.2%}.")
    return LimitResult(
        limit_name="daily_loss_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Daily loss is within budget.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_total_drawdown(
    snapshot: PortfolioRiskSnapshot, policy: EffectiveRiskPolicy
) -> LimitResult:
    """Evaluate a portfolio snapshot's total-drawdown ceiling against policy.

    Args:
        snapshot: Canonical portfolio-level risk snapshot.
        policy: Resolved effective risk policy providing the total-loss cap.

    Returns:
        LimitResult: BLOCK on breach, APPROVE otherwise.
    """
    logger.info("Checking canonical total drawdown ceiling.")
    limit = policy.resolved_config.max_total_loss_pct
    if snapshot.drawdown >= limit:
        logger.info(f"Canonical total drawdown breached: {snapshot.drawdown:.2%}.")
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.DRAWDOWN_BREACH,
            message=(
                f"Total drawdown ceiling breached: {snapshot.drawdown:.2%} >= "
                f"{limit:.2%}."
            ),
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
            details={"drawdown": float(snapshot.drawdown)},
        )

    logger.debug(
        f"Canonical total drawdown is within ceiling: {snapshot.drawdown:.2%}."
    )
    return LimitResult(
        limit_name="max_drawdown_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Total drawdown is within ceiling.",
        severity=RiskSeverity.INFO,
        breached=False,
    )


def check_exposure_limits(
    projected: PortfolioRiskSnapshot, policy: EffectiveRiskPolicy
) -> tuple[LimitResult, ...]:
    """Evaluate portfolio-level exposure against the resolved policy.

    Args:
        projected: Canonical projected portfolio-level risk snapshot.
        policy: Resolved effective risk policy providing the exposure cap.

    Returns:
        tuple[LimitResult, ...]: Portfolio exposure result. Symbol/currency/
            cluster-level breakdowns are evaluated separately by
            :func:`check_symbol_exposure_limit`, :func:`check_currency_exposure_limit`,
            and :func:`check_correlation_limit` once per-leg canonical snapshots
            are available on the request.
    """
    logger.info("Checking canonical portfolio exposure limits.")
    equity_relative_cap = policy.resolved_config.risk.max_total_open_risk
    if equity_relative_cap <= 0:
        results: tuple[LimitResult, ...] = (
            LimitResult(
                limit_name="portfolio_exposure_limit",
                status=RiskDecisionStatus.APPROVE,
                reason_code=RiskReasonCode.OK,
                message="No portfolio exposure cap configured.",
                severity=RiskSeverity.INFO,
                breached=False,
            ),
        )
        return results

    breached = projected.exposure > equity_relative_cap
    logger.debug(f"Canonical portfolio exposure breached={breached}.")
    result = LimitResult(
        limit_name="portfolio_exposure_limit",
        status=RiskDecisionStatus.REJECT if breached else RiskDecisionStatus.APPROVE,
        reason_code=(
            RiskReasonCode.CONCENTRATION_BREACH if breached else RiskReasonCode.OK
        ),
        message=(
            f"Portfolio exposure {projected.exposure} exceeds cap "
            f"{equity_relative_cap}."
            if breached
            else "Portfolio exposure is within concentration ceilings."
        ),
        severity=RiskSeverity.HARD_BREACH if breached else RiskSeverity.INFO,
        breached=breached,
        details={"exposure": float(projected.exposure)},
    )
    return (result,)


def check_tail_risk_limits(
    var: VaRSnapshot,
    es: ExpectedShortfallSnapshot,
    stress: StressSummary,
    policy: EffectiveRiskPolicy,
) -> tuple[LimitResult, ...]:
    """Evaluate VaR, Expected Shortfall, and stress-loss limits together.

    Args:
        var: Calculated Value-at-Risk snapshot.
        es: Calculated Expected Shortfall snapshot.
        stress: Summary of all evaluated stress scenarios.
        policy: Resolved effective risk policy providing tail-risk caps.

    Returns:
        tuple[LimitResult, ...]: VaR, ES, and stress-loss results in that order.
    """
    logger.info("Checking canonical tail-risk limits (VaR/ES/stress).")
    tail_risk_cfg = policy.resolved_config.tail_risk
    equity_basis = var.exposure if var.exposure > 0 else Decimal("1.0")

    var_ratio = var.result / equity_basis
    var_breached = var_ratio > tail_risk_cfg.max_portfolio_var
    var_result = LimitResult(
        limit_name="var_limit",
        status=(
            RiskDecisionStatus.REJECT if var_breached else RiskDecisionStatus.APPROVE
        ),
        reason_code=RiskReasonCode.VAR_BREACH if var_breached else RiskReasonCode.OK,
        message=(
            f"Value-at-Risk ratio {var_ratio:.2%} exceeds cap "
            f"{tail_risk_cfg.max_portfolio_var:.2%}."
            if var_breached
            else "Value-at-Risk is within safe bounds."
        ),
        severity=RiskSeverity.HARD_BREACH if var_breached else RiskSeverity.INFO,
        breached=var_breached,
        details={"var_ratio": float(var_ratio)},
    )

    es_ratio = es.average_tail_loss / equity_basis
    es_breached = es_ratio > tail_risk_cfg.max_portfolio_es
    es_result = LimitResult(
        limit_name="expected_shortfall_limit",
        status=(
            RiskDecisionStatus.REJECT if es_breached else RiskDecisionStatus.APPROVE
        ),
        reason_code=RiskReasonCode.ES_BREACH if es_breached else RiskReasonCode.OK,
        message=(
            f"Expected Shortfall ratio {es_ratio:.2%} exceeds cap "
            f"{tail_risk_cfg.max_portfolio_es:.2%}."
            if es_breached
            else "Expected Shortfall is within safe bounds."
        ),
        severity=RiskSeverity.HARD_BREACH if es_breached else RiskSeverity.INFO,
        breached=es_breached,
        details={"es_ratio": float(es_ratio)},
    )

    stress_result = LimitResult(
        limit_name="stress_loss_limit",
        status=(
            RiskDecisionStatus.APPROVE
            if stress.pass_status
            else RiskDecisionStatus.REJECT
        ),
        reason_code=(
            RiskReasonCode.OK if stress.pass_status else RiskReasonCode.STRESS_BREACH
        ),
        message=(
            "Stress scenarios are within survival capacity."
            if stress.pass_status
            else f"Stress scenarios breached: {stress.reason_codes}."
        ),
        severity=RiskSeverity.INFO if stress.pass_status else RiskSeverity.HARD_BREACH,
        breached=not stress.pass_status,
        details={"reason_codes": list(stress.reason_codes)},
    )

    logger.debug(
        f"Canonical tail-risk results: var_breached={var_breached}, "
        f"es_breached={es_breached}, stress_pass={stress.pass_status}."
    )
    return (var_result, es_result, stress_result)


def check_execution_limits(
    execution: ExecutionRiskSnapshot, policy: EffectiveRiskPolicy
) -> tuple[LimitResult, ...]:
    """Evaluate spread, marketability, and lot-step limits from a snapshot.

    Args:
        execution: Calculated execution risk snapshot.
        policy: Resolved effective risk policy providing the spread cap.

    Returns:
        tuple[LimitResult, ...]: Marketability and spread results in that
            order. Frequency and pending-order limits are evaluated by
            :func:`check_trade_frequency_limit` and
            :func:`check_pending_order_limit` once request-level evidence is
            available.
    """
    logger.info("Checking canonical execution feasibility limits.")
    config = policy.resolved_config

    marketability_result = LimitResult(
        limit_name="spread_limit",
        status=(
            RiskDecisionStatus.APPROVE
            if execution.marketability
            else RiskDecisionStatus.REJECT
        ),
        reason_code=(
            RiskReasonCode.OK
            if execution.marketability
            else RiskReasonCode.SPREAD_BREACH
        ),
        message=(
            "Market session permits execution."
            if execution.marketability
            else "Market session is closed or suspended."
        ),
        severity=(
            RiskSeverity.INFO if execution.marketability else RiskSeverity.HARD_BREACH
        ),
        breached=not execution.marketability,
    )

    max_spread_multiplier = config.max_spread_multiplier
    spread_cap = execution.slippage * max_spread_multiplier
    spread_breached = max_spread_multiplier > 0 and execution.spread > spread_cap
    spread_result = LimitResult(
        limit_name="slippage_limit",
        status=(
            RiskDecisionStatus.REJECT if spread_breached else RiskDecisionStatus.APPROVE
        ),
        reason_code=(
            RiskReasonCode.SPREAD_BREACH if spread_breached else RiskReasonCode.OK
        ),
        message=(
            f"Spread {execution.spread} exceeds slippage-relative cap {spread_cap}."
            if spread_breached
            else "Spread/slippage relationship is within policy bounds."
        ),
        severity=(RiskSeverity.HARD_BREACH if spread_breached else RiskSeverity.INFO),
        breached=spread_breached,
        details={
            "spread": float(execution.spread),
            "slippage": float(execution.slippage),
        },
    )

    logger.debug(
        f"Canonical execution limits: marketability={execution.marketability}, "
        f"spread_breached={spread_breached}."
    )
    return (marketability_result, spread_result)
