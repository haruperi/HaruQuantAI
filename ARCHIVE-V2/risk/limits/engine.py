"""Ordered limit-check orchestration.

Runs the immutable, stable-order sequence of pure limit checks, selects the
principal failing result, and composes deterministic composite-breach flags
so the governor receives a repeatable and explainable limit outcome.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.services.risk.limits.checks import (
    check_correlation_limit,
    check_currency_exposure_limit,
    check_daily_loss_limit,
    check_expected_shortfall_limit,
    check_kill_switch_state,
    check_leverage_limit,
    check_margin_limit,
    check_max_drawdown_limit,
    check_news_blackout,
    check_pending_order_limit,
    check_portfolio_exposure_limit,
    check_rollover_blackout,
    check_slippage_limit,
    check_spread_limit,
    check_stale_evidence_limit,
    check_strategy_loss_limit,
    check_stress_loss_limit,
    check_symbol_exposure_limit,
    check_trade_frequency_limit,
    check_var_limit,
)
from app.services.risk.limits.contracts import (
    DEFAULT_LIMIT_PRECEDENCE,
    LimitAssessment,
    LimitCheck,
    LimitContext,
    LimitPrecedence,
    LimitResult,
)
from app.services.risk.models import (
    RiskAssessmentRequest,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)
from app.utils.logger import logger

ORDERED_LIMIT_CHECKS: tuple[LimitCheck, ...] = (
    LimitCheck(
        limit_name="kill_switch_state",
        severity=RiskSeverity.EMERGENCY_HALT,
        precedence=0,
        evaluator=check_kill_switch_state,
    ),
    LimitCheck(
        limit_name="stale_evidence",
        severity=RiskSeverity.HARD_BREACH,
        precedence=1,
        evaluator=check_stale_evidence_limit,
    ),
    LimitCheck(
        limit_name="max_drawdown_limit",
        severity=RiskSeverity.CRITICAL_BREACH,
        precedence=2,
        evaluator=check_max_drawdown_limit,
    ),
    LimitCheck(
        limit_name="daily_loss_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=3,
        evaluator=check_daily_loss_limit,
    ),
    LimitCheck(
        limit_name="strategy_loss_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=4,
        evaluator=check_strategy_loss_limit,
    ),
    LimitCheck(
        limit_name="news_blackout",
        severity=RiskSeverity.HARD_BREACH,
        precedence=5,
        evaluator=check_news_blackout,
    ),
    LimitCheck(
        limit_name="rollover_blackout",
        severity=RiskSeverity.HARD_BREACH,
        precedence=6,
        evaluator=check_rollover_blackout,
    ),
    LimitCheck(
        limit_name="spread_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=7,
        evaluator=check_spread_limit,
    ),
    LimitCheck(
        limit_name="slippage_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=8,
        evaluator=check_slippage_limit,
    ),
    LimitCheck(
        limit_name="trade_frequency_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=9,
        evaluator=check_trade_frequency_limit,
    ),
    LimitCheck(
        limit_name="pending_order_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=10,
        evaluator=check_pending_order_limit,
    ),
    LimitCheck(
        limit_name="portfolio_exposure_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=11,
        evaluator=check_portfolio_exposure_limit,
    ),
    LimitCheck(
        limit_name="symbol_exposure_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=12,
        evaluator=check_symbol_exposure_limit,
    ),
    LimitCheck(
        limit_name="currency_exposure_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=13,
        evaluator=check_currency_exposure_limit,
    ),
    LimitCheck(
        limit_name="correlated_cluster_limit",
        required_evidence=("portfolio_correlation",),
        severity=RiskSeverity.HARD_BREACH,
        precedence=14,
        evaluator=check_correlation_limit,
    ),
    LimitCheck(
        limit_name="var_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=15,
        evaluator=check_var_limit,
    ),
    LimitCheck(
        limit_name="expected_shortfall_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=16,
        evaluator=check_expected_shortfall_limit,
    ),
    LimitCheck(
        limit_name="stress_loss_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=17,
        evaluator=check_stress_loss_limit,
    ),
    LimitCheck(
        limit_name="leverage_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=18,
        evaluator=check_leverage_limit,
    ),
    LimitCheck(
        limit_name="margin_limit",
        severity=RiskSeverity.HARD_BREACH,
        precedence=19,
        evaluator=check_margin_limit,
    ),
)
"""Immutable, deterministic evaluation sequence. Assembled here (rather than
in contracts.py) because building it requires the concrete evaluator
functions from :mod:`app.services.risk.limits.checks`, and contracts.py must
stay import-independent of checks.py to avoid a circular import."""

REGISTERED_LIMIT_NAMES: set[str] = {
    "kill_switch_state",
    "stale_evidence",
    "max_drawdown_limit",
    "daily_loss_limit",
    "strategy_loss_limit",
    "news_blackout",
    "rollover_blackout",
    "spread_limit",
    "slippage_limit",
    "trade_frequency_limit",
    "pending_order_limit",
    "portfolio_exposure_limit",
    "symbol_exposure_limit",
    "currency_exposure_limit",
    "correlated_cluster_limit",
    "var_limit",
    "expected_shortfall_limit",
    "stress_loss_limit",
    "leverage_limit",
    "margin_limit",
    "check_kill_switch_state",
    "check_stale_evidence_limit",
    "check_max_drawdown_limit",
    "check_daily_loss_limit",
    "check_strategy_loss_limit",
    "check_news_blackout",
    "check_rollover_blackout",
    "check_spread_limit",
    "check_slippage_limit",
    "check_trade_frequency_limit",
    "check_pending_order_limit",
    "check_portfolio_exposure_limit",
    "check_symbol_exposure_limit",
    "check_currency_exposure_limit",
    "check_correlation_limit",
    "check_var_limit",
    "check_expected_shortfall_limit",
    "check_stress_loss_limit",
    "check_leverage_limit",
    "check_margin_limit",
    "stale_evidence_limit",
    "correlation_limit",
}

FUNCTION_TO_LIMIT_NAMES: dict[str, set[str]] = {
    "kill_switch_state": {"kill_switch_state"},
    "stale_evidence": {"stale_evidence", "stale_evidence_limit"},
    "max_drawdown_limit": {"max_drawdown_limit"},
    "daily_loss_limit": {"daily_loss_limit"},
    "strategy_loss_limit": {"strategy_loss_limit"},
    "news_blackout": {"news_blackout"},
    "rollover_blackout": {"rollover_blackout"},
    "spread_limit": {"spread_limit"},
    "slippage_limit": {"slippage_limit"},
    "trade_frequency_limit": {"trade_frequency_limit"},
    "pending_order_limit": {"pending_order_limit"},
    "portfolio_exposure_limit": {"portfolio_exposure_limit"},
    "symbol_exposure_limit": {"symbol_exposure_limit"},
    "currency_exposure_limit": {"currency_exposure_limit"},
    "correlated_cluster_limit": {"correlated_cluster_limit", "correlation_limit"},
    "var_limit": {"var_limit"},
    "expected_shortfall_limit": {"expected_shortfall_limit"},
    "stress_loss_limit": {"stress_loss_limit"},
    "leverage_limit": {"leverage_limit"},
    "margin_limit": {"margin_limit"},
}
"""Maps each check's canonical `limit_name` to every alias accepted in
`run_limits`/`enabled_limits` request filters, preserving v1 alias behavior."""


class LimitEngine:
    """Consolidated runner executing and aggregating limits check pipelines."""

    def __init__(self, config: RiskConfig) -> None:
        """Initialize engine with active risk config.

        Args:
            config: Active risk configuration profile.
        """
        self.config = config
        logger.debug("LimitEngine initialized.")

    def execute(self, request: RiskAssessmentRequest) -> list[LimitResult]:
        """Execute the full, ordered sequence of limit checks.

        Args:
            request: The current evaluation state containing context snapshots.

        Returns:
            list[LimitResult]: Result outcomes of all checkpoints.
        """
        logger.info("Executing ordered limit-check sequence.")
        enabled_limits = request.market_context.get("enabled_limits")
        run_limits = request.market_context.get("run_limits")

        checked_limits: list[Any] = []
        if isinstance(enabled_limits, list | tuple | set):
            checked_limits.extend(enabled_limits)
        if isinstance(run_limits, list | tuple | set):
            checked_limits.extend(run_limits)

        unknown_names = [
            name for name in checked_limits if name not in REGISTERED_LIMIT_NAMES
        ]
        if unknown_names:
            logger.error(f"Unknown limit name(s) in request: {unknown_names}")
            msg = (
                f"Unknown limit name(s) in run_limits/enabled_limits: "
                f"{', '.join(map(str, unknown_names))}"
            )
            return [
                LimitResult(
                    limit_name="invalid_limit_name",
                    status=RiskDecisionStatus.BLOCK,
                    reason_code=RiskReasonCode.INVALID_INPUT,
                    message=msg,
                    severity=RiskSeverity.CRITICAL_BREACH,
                    breached=True,
                )
            ]

        run_set = set(checked_limits)

        results = []
        for check in ORDERED_LIMIT_CHECKS:
            func_name = getattr(check.evaluator, "__name__", "")
            if run_set:
                func_names = {
                    check.limit_name,
                    func_name,
                    func_name.replace("check_", ""),
                }
                func_names.update(FUNCTION_TO_LIMIT_NAMES.get(check.limit_name, set()))
                if not (func_names & run_set):
                    continue

            try:
                res = check.evaluator(request, self.config)
                results.append(res)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Limit check failure in '{check.limit_name}': {e}")
                results.append(
                    LimitResult(
                        limit_name=check.limit_name,
                        status=RiskDecisionStatus.BLOCK,
                        reason_code=RiskReasonCode.UNEXPECTED_ERROR,
                        message=f"Limit check calculation failed: {e}",
                        severity=RiskSeverity.CRITICAL_BREACH,
                        breached=True,
                    )
                )
        return results


def run_limit_checks(
    request: RiskAssessmentRequest,
    risk_config: RiskConfig | None = None,
) -> tuple[
    RiskDecisionStatus,
    RiskReasonCode,
    str,
    list[str],
    str,
    list[LimitResult],
]:
    """Stateless runner function evaluating all limit checks and aggregating.

    Args:
        request: The active risk assessment request.
        risk_config: Optional configuration override.

    Returns:
        tuple[status, reason_code, message, composite_breach_flags,
              primary_failure_limit, limit_results]
    """
    logger.info("Running stateless limit-check aggregation.")
    config = risk_config or request.risk_config
    engine = LimitEngine(config=config)
    results = engine.execute(request)

    # Precedence scoring:
    # blocked > fail > needs_more_evidence > warn > pass
    # 0: BLOCK (blocked)
    # 1: REJECT (fail)
    # 2: NEEDS_MORE_EVIDENCE
    # 3: NEEDS_APPROVAL / REDUCE_SIZE / WARNING (warn)
    # 4: APPROVE / OK (pass)
    aggregated_status = RiskDecisionStatus.APPROVE
    reason_code = RiskReasonCode.OK
    message = "All limit checks cleared."
    primary_failure_limit = ""
    composite_breach_flags = []

    status_ranks = {
        RiskDecisionStatus.BLOCK: 0.0,
        RiskDecisionStatus.REJECT: 1.0,
        RiskDecisionStatus.NEEDS_MORE_EVIDENCE: 2.0,
        RiskDecisionStatus.NEEDS_APPROVAL: 3.0,
        RiskDecisionStatus.REDUCE_SIZE: 3.5,
    }

    worst_rank = 4.0

    for res in results:
        if res.breached or res.status != RiskDecisionStatus.APPROVE:
            composite_breach_flags.append(res.limit_name)

        current_rank = status_ranks.get(res.status, 4.0)
        if res.severity == RiskSeverity.WARNING and res.breached:
            current_rank = 3.8

        if current_rank < worst_rank:
            worst_rank = current_rank
            aggregated_status = res.status
            reason_code = res.reason_code
            message = res.message
            primary_failure_limit = res.limit_name

    warning_flags = [
        r.limit_name
        for r in results
        if r.severity == RiskSeverity.WARNING and r.breached
    ]
    for w in warning_flags:
        if w not in composite_breach_flags:
            composite_breach_flags.append(w)

    logger.debug(
        f"Aggregated limit status={aggregated_status}, "
        f"primary_failure='{primary_failure_limit}'."
    )
    return (
        aggregated_status,
        reason_code,
        message,
        sorted(composite_breach_flags),
        primary_failure_limit,
        results,
    )


def check_risk_limits(
    request: RiskAssessmentRequest,
    config: RiskConfig,
) -> list[LimitResult]:
    """Evaluate all configured risk limits sequentially.

    Args:
        request: The active risk assessment request.
        config: The RiskConfig config profile.

    Returns:
        list[LimitResult]: The results of evaluating each limit check.
    """
    logger.info("check_risk_limits entry.")
    engine = LimitEngine(config=config)
    return engine.execute(request)


def select_primary_failure(
    results: Sequence[LimitResult],
    precedence: LimitPrecedence = DEFAULT_LIMIT_PRECEDENCE,
) -> LimitResult | None:
    """Select the stable principal failing result from a set of limit results.

    Args:
        results: Ordered limit-check results.
        precedence: Status-to-rank mapping; lower rank wins. Defaults to
            :data:`~app.services.risk.limits.contracts.DEFAULT_LIMIT_PRECEDENCE`.

    Returns:
        LimitResult | None: The stable worst result, or None if every result
            is a plain APPROVE (i.e. nothing failed or warned).
    """
    logger.info("Selecting stable primary failure from limit results.")
    approve_rank = precedence.get(RiskDecisionStatus.APPROVE, 4)
    best: LimitResult | None = None
    best_rank = approve_rank
    for res in results:
        rank = precedence.get(res.status, approve_rank)
        if rank < best_rank:
            best_rank = rank
            best = res

    logger.debug(f"Primary failure selected: {best.limit_name if best else None}.")
    return best


def build_composite_breach_flags(
    results: Sequence[LimitResult],
) -> frozenset[RiskReasonCode]:
    """Compose deterministic composite breach flags from limit results.

    Args:
        results: Ordered limit-check results.

    Returns:
        frozenset[RiskReasonCode]: Distinct reason codes across all
            breached or non-approve results.
    """
    logger.info("Building composite breach flags from limit results.")
    flags = {
        res.reason_code
        for res in results
        if res.breached or res.status != RiskDecisionStatus.APPROVE
    }
    logger.debug(f"Composite breach flags: {flags}.")
    return frozenset(flags)


def evaluate_ordered_limits(
    context: LimitContext,
    checks_sequence: tuple[LimitCheck, ...] = ORDERED_LIMIT_CHECKS,
) -> LimitAssessment:
    """Run the immutable ordered-check sequence and aggregate outcomes.

    Args:
        context: Canonical risk-assessment request evidence.
        checks_sequence: The ordered sequence of checks to run. Defaults to
            the full :data:`ORDERED_LIMIT_CHECKS` registry.

    Returns:
        LimitAssessment: Aggregated results, status, primary failure, and
            composite breach flags.
    """
    logger.info("Evaluating ordered limits into a canonical LimitAssessment.")
    results: list[LimitResult] = []
    for check in checks_sequence:
        try:
            results.append(check.evaluator(context, context.risk_config))
        except Exception as e:  # noqa: BLE001
            logger.error(f"Limit check failure in '{check.limit_name}': {e}")
            results.append(
                LimitResult(
                    limit_name=check.limit_name,
                    status=RiskDecisionStatus.BLOCK,
                    reason_code=RiskReasonCode.UNEXPECTED_ERROR,
                    message=f"Limit check calculation failed: {e}",
                    severity=RiskSeverity.CRITICAL_BREACH,
                    breached=True,
                )
            )

    primary_failure = select_primary_failure(results)
    status = primary_failure.status if primary_failure else RiskDecisionStatus.APPROVE
    breach_flags = build_composite_breach_flags(results)

    logger.debug(f"LimitAssessment status={status}, breach_flags={breach_flags}.")
    return LimitAssessment(
        results=tuple(results),
        status=status,
        primary_failure=primary_failure,
        composite_breach_flags=breach_flags,
    )
