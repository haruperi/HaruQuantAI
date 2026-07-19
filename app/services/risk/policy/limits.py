"""Deterministic portfolio and supplied market-context Risk limit evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    LimitStatus,
    PortfolioRiskSnapshot,
    RiskDomainError,
    RiskErrorCode,
    RiskLimitResult,
    validate_market_context_evidence,
)
from app.utils import logger

if TYPE_CHECKING:
    from app.services.data.contracts import MarketContextEvidence


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If the timestamp is not aware UTC.
    """
    logger.debug("Validating Policy evaluation UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("policy evaluation time must be aware UTC")
    return value


def _result(
    limit_id: str,
    status: LimitStatus,
    observed: Decimal | None,
    threshold: Decimal | None,
    evidence_refs: tuple[str, ...],
    precedence: int,
    *,
    reason: RiskErrorCode | None = None,
) -> RiskLimitResult:
    """Build one ordered limit result.

    Args:
        limit_id: Stable limit identity.
        status: Evaluation status.
        observed: Observed numeric value when applicable.
        threshold: Applied threshold when applicable.
        evidence_refs: Exact evidence references.
        precedence: Stable evaluation order.
        reason: Required failing reason code.

    Returns:
        Immutable ordered limit result.
    """
    logger.debug("Building ordered Policy limit result: %s", limit_id)
    return RiskLimitResult(
        limit_id=limit_id,
        status=status,
        observed_value=observed,
        threshold_value=threshold,
        reason_code=reason,
        evidence_refs=evidence_refs,
        precedence=precedence,
    )


def _threshold_result(
    limit_id: str,
    observed: Decimal | None,
    threshold: Decimal | None,
    evidence_refs: tuple[str, ...],
    precedence: int,
) -> RiskLimitResult:
    """Evaluate an optional upper-bound threshold.

    Args:
        limit_id: Stable limit identity.
        observed: Observed value or None when evidence is missing.
        threshold: Applied upper bound or None when disabled.
        evidence_refs: Exact evidence references.
        precedence: Stable evaluation order.

    Returns:
        Pass, failure, or needs-evidence result.
    """
    logger.debug("Evaluating upper-bound Policy limit: %s", limit_id)
    if threshold is None:
        return _result(
            limit_id,
            LimitStatus.PASS,
            observed,
            None,
            evidence_refs,
            precedence,
        )
    if observed is None:
        return _result(
            limit_id,
            LimitStatus.NEEDS_MORE_EVIDENCE,
            None,
            threshold,
            evidence_refs,
            precedence,
            reason=RiskErrorCode.MISSING_EVIDENCE,
        )
    status = LimitStatus.FAIL if observed > threshold else LimitStatus.PASS
    return _result(
        limit_id,
        status,
        observed,
        threshold,
        evidence_refs,
        precedence,
        reason=RiskErrorCode.LIMIT_FAILED if status is LimitStatus.FAIL else None,
    )


def _loss_ratio(loss: Decimal, equity: Decimal) -> Decimal:
    """Calculate loss against its embedded reference equity.

    Args:
        loss: Non-negative monetary loss.
        equity: Current equity.

    Returns:
        Exact loss ratio, with depleted equity represented as one.
    """
    logger.debug("Calculating Policy loss ratio against reference equity")
    reference = equity + loss
    return Decimal(1) if reference <= 0 else loss / reference


def _freshness_result(
    as_of: datetime,
    now: datetime,
    max_age_seconds: int,
    evidence_refs: tuple[str, ...],
) -> RiskLimitResult:
    """Evaluate deterministic evidence freshness.

    Args:
        as_of: Evidence observation time.
        now: Injected evaluation time.
        max_age_seconds: Maximum permitted age.
        evidence_refs: Exact evidence references.

    Returns:
        Ordered freshness result.
    """
    logger.debug("Evaluating Policy evidence freshness")
    age = Decimal(str((now - as_of).total_seconds()))
    threshold = Decimal(max_age_seconds)
    if age < 0 or age > threshold:
        return _result(
            "freshness",
            LimitStatus.BLOCKED,
            age,
            threshold,
            evidence_refs,
            0,
            reason=RiskErrorCode.STALE_EVIDENCE,
        )
    return _result(
        "freshness",
        LimitStatus.PASS,
        age,
        threshold,
        evidence_refs,
        0,
    )


def _consistency_result(
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    evidence_refs: tuple[str, ...],
) -> RiskLimitResult:
    """Evaluate snapshot gaps, embedded statuses, equity, and config binding.

    Args:
        snapshot: Immutable portfolio measurements.
        config: Active Risk policy.
        evidence_refs: Exact snapshot evidence references.

    Returns:
        Ordered consistency result.
    """
    logger.debug("Evaluating Policy snapshot consistency")
    failing_statuses = {LimitStatus.FAIL, LimitStatus.BLOCKED}
    inconsistent = (
        snapshot.equity <= 0
        or bool(snapshot.gaps)
        or any(item in failing_statuses for item in snapshot.limit_statuses.values())
        or snapshot.config_hash != compute_config_hash(config)
    )
    return _result(
        "consistency",
        LimitStatus.FAIL if inconsistent else LimitStatus.PASS,
        None,
        None,
        evidence_refs,
        1,
        reason=RiskErrorCode.LIMIT_FAILED if inconsistent else None,
    )


def _concentration_results(
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    evidence_refs: tuple[str, ...],
    start_precedence: int,
) -> tuple[RiskLimitResult, ...]:
    """Evaluate symbol then other-dimension concentration in stable key order.

    Args:
        snapshot: Immutable portfolio measurements.
        config: Active Risk policy.
        evidence_refs: Exact snapshot evidence references.
        start_precedence: First concentration precedence.

    Returns:
        Ordered per-dimension concentration results.
    """
    logger.debug("Evaluating Policy concentration limits")
    symbols = sorted(
        key for key in snapshot.exposure_by_dimension if key.startswith("symbol:")
    )
    others = sorted(
        key for key in snapshot.exposure_by_dimension if not key.startswith("symbol:")
    )
    results: list[RiskLimitResult] = []
    for offset, key in enumerate((*symbols, *others)):
        default = (
            config.max_symbol_concentration
            if key.startswith("symbol:")
            else config.max_dimension_concentration
        )
        threshold = config.allocation_caps.get(key, default)
        observed = (
            Decimal(0)
            if snapshot.gross_exposure == 0
            else abs(snapshot.exposure_by_dimension[key]) / snapshot.gross_exposure
        )
        results.append(
            _threshold_result(
                f"concentration:{key}",
                observed,
                threshold,
                evidence_refs,
                start_precedence + offset,
            )
        )
    return tuple(results)


def evaluate_portfolio_limits(
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    *,
    now: datetime,
) -> tuple[RiskLimitResult, ...]:
    """Evaluate portfolio limits in the authoritative deterministic precedence.

    Args:
        snapshot: Immutable portfolio Risk measurements.
        config: Active validated Risk policy.
        now: Injected current UTC time.

    Returns:
        Complete ordered limit results; the first failing item is primary.

    Raises:
        RiskDomainError: If required configuration or evaluation time is invalid.
    """
    logger.info("Evaluating deterministic portfolio Policy limits")
    try:
        checked_now = _utc(now)
        max_age = config.evidence_max_age_seconds["portfolio"]
        evidence_refs = tuple(snapshot.evidence_refs.values()) or (
            snapshot.snapshot_id,
        )
        results = [
            _freshness_result(snapshot.as_of, checked_now, max_age, evidence_refs),
            _consistency_result(snapshot, config, evidence_refs),
            _threshold_result(
                "daily_loss",
                _loss_ratio(snapshot.daily_loss, snapshot.equity),
                config.max_daily_loss,
                evidence_refs,
                2,
            ),
            _threshold_result(
                "total_loss",
                _loss_ratio(snapshot.total_loss, snapshot.equity),
                config.max_total_loss,
                evidence_refs,
                3,
            ),
            _threshold_result(
                "drawdown",
                snapshot.drawdown,
                config.max_drawdown,
                evidence_refs,
                4,
            ),
        ]
        concentrations = _concentration_results(
            snapshot, config, evidence_refs, len(results)
        )
        results.extend(concentrations)
        precedence = len(results)
        results.extend(
            (
                _threshold_result(
                    "margin_utilization",
                    snapshot.margin_utilization,
                    config.max_margin_utilization,
                    evidence_refs,
                    precedence,
                ),
                _threshold_result(
                    "effective_leverage",
                    snapshot.effective_leverage,
                    config.max_effective_leverage,
                    evidence_refs,
                    precedence + 1,
                ),
                _threshold_result(
                    "historical_var",
                    None
                    if snapshot.historical_var is None or snapshot.equity <= 0
                    else snapshot.historical_var / snapshot.equity,
                    config.max_historical_var_ratio,
                    evidence_refs,
                    precedence + 2,
                ),
                _threshold_result(
                    "historical_cvar",
                    None
                    if snapshot.historical_cvar is None or snapshot.equity <= 0
                    else snapshot.historical_cvar / snapshot.equity,
                    config.max_historical_cvar_ratio,
                    evidence_refs,
                    precedence + 3,
                ),
                _threshold_result(
                    "correlation",
                    snapshot.portfolio_correlation,
                    config.max_correlation,
                    evidence_refs,
                    precedence + 4,
                ),
            )
        )
        return tuple(results)
    except RiskDomainError:
        logger.error("Portfolio Policy limit evaluation failed closed")
        raise
    except (KeyError, TypeError, ValueError) as error:
        logger.error("Portfolio Policy configuration is incomplete")
        raise RiskDomainError(
            RiskErrorCode.INVALID_RISK_CONFIG,
            "portfolio limit policy configuration invalid",
        ) from error


def _calendar_missing_result(
    mode: str,
    evidence_refs: tuple[str, ...],
    precedence: int,
) -> RiskLimitResult:
    """Apply the configured missing-calendar mode.

    Args:
        mode: Configured missing-evidence behavior.
        evidence_refs: Exact market evidence references.
        precedence: Stable evaluation order.

    Returns:
        Configured calendar result.
    """
    logger.debug("Applying missing calendar Policy mode")
    status = {
        "ignore": LimitStatus.PASS,
        "warn": LimitStatus.WARN,
        "needs_more_evidence": LimitStatus.NEEDS_MORE_EVIDENCE,
        "block": LimitStatus.BLOCKED,
    }[mode]
    reason = (
        RiskErrorCode.MISSING_EVIDENCE
        if status is LimitStatus.NEEDS_MORE_EVIDENCE
        else RiskErrorCode.POLICY_BLOCKED
        if status is LimitStatus.BLOCKED
        else None
    )
    return _result(
        "calendar",
        status,
        None,
        None,
        evidence_refs,
        precedence,
        reason=reason,
    )


def _session_result(
    evidence: MarketContextEvidence,
    config: RiskConfig,
    evidence_refs: tuple[str, ...],
) -> RiskLimitResult:
    """Evaluate exact timezone and normalized session state.

    Args:
        evidence: Supplied Data-owned context.
        config: Active Risk policy.
        evidence_refs: Exact evidence references.

    Returns:
        Ordered session result.
    """
    logger.debug("Evaluating normalized market session Policy")
    if config.session_timezone is None:
        return _result("session", LimitStatus.PASS, None, None, evidence_refs, 1)
    try:
        ZoneInfo(evidence.timezone)
    except ZoneInfoNotFoundError:
        return _result(
            "session",
            LimitStatus.BLOCKED,
            None,
            None,
            evidence_refs,
            1,
            reason=RiskErrorCode.POLICY_BLOCKED,
        )
    if evidence.session_state is None or evidence.session_state == "unknown":
        return _result(
            "session",
            LimitStatus.NEEDS_MORE_EVIDENCE,
            None,
            None,
            evidence_refs,
            1,
            reason=RiskErrorCode.MISSING_EVIDENCE,
        )
    allowed = (
        evidence.timezone == config.session_timezone
        and evidence.session_state in config.allowed_session_states
    )
    return _result(
        "session",
        LimitStatus.PASS if allowed else LimitStatus.BLOCKED,
        None,
        None,
        evidence_refs,
        1,
        reason=None if allowed else RiskErrorCode.POLICY_BLOCKED,
    )


def _calendar_result(
    evidence: MarketContextEvidence,
    config: RiskConfig,
    evidence_refs: tuple[str, ...],
) -> RiskLimitResult:
    """Evaluate normalized calendar state and blackout provenance.

    Args:
        evidence: Supplied Data-owned context.
        config: Active Risk policy.
        evidence_refs: Exact evidence references.

    Returns:
        Ordered calendar result.
    """
    logger.debug("Evaluating normalized market calendar Policy")
    mode = config.missing_calendar_mode
    if mode is None:
        return _result("calendar", LimitStatus.PASS, None, None, evidence_refs, 2)
    provenance_matches = evidence.provenance.get("blackout_before_minutes") == str(
        config.news_blackout_before_minutes
    ) and evidence.provenance.get("blackout_after_minutes") == str(
        config.news_blackout_after_minutes
    )
    if (
        evidence.calendar_state is None
        or evidence.calendar_state == "unknown"
        or not provenance_matches
    ):
        return _calendar_missing_result(mode, evidence_refs, 2)
    blocked = evidence.calendar_state in config.blocked_calendar_states
    return _result(
        "calendar",
        LimitStatus.BLOCKED if blocked else LimitStatus.PASS,
        None,
        None,
        evidence_refs,
        2,
        reason=RiskErrorCode.POLICY_BLOCKED if blocked else None,
    )


def _spread_result(
    evidence: MarketContextEvidence,
    caps: Mapping[str, Decimal],
    evidence_refs: tuple[str, ...],
) -> RiskLimitResult:
    """Evaluate an exact-unit spread cap without conversion.

    Args:
        evidence: Supplied Data-owned context.
        caps: Exact configured spread caps.
        evidence_refs: Exact evidence references.

    Returns:
        Ordered spread result.
    """
    logger.debug("Evaluating exact-unit market spread Policy")
    if evidence.spread_unit is None:
        return _result("spread", LimitStatus.PASS, None, None, evidence_refs, 3)
    threshold = caps.get(
        f"{evidence.symbol}@{evidence.spread_unit}",
        caps.get(f"*@{evidence.spread_unit}"),
    )
    return _threshold_result("spread", evidence.spread, threshold, evidence_refs, 3)


def evaluate_market_context(
    evidence: MarketContextEvidence,
    config: RiskConfig,
    *,
    now: datetime,
) -> tuple[RiskLimitResult, ...]:
    """Evaluate only supplied V1 market context in deterministic precedence.

    Args:
        evidence: Data-owned immutable market context.
        config: Active validated Risk policy.
        now: Injected current UTC time.

    Returns:
        Ordered freshness, session, calendar, spread, and liquidity results.

    Raises:
        RiskDomainError: If evidence is incompatible, stale, or policy is invalid.
    """
    logger.info("Evaluating supplied market-context Policy limits")
    checked_now = _utc(now)
    validate_market_context_evidence(evidence, now=checked_now)
    try:
        max_age = config.evidence_max_age_seconds["market"]
        evidence_refs = (evidence.request_id,)
        liquidity_status = (
            LimitStatus.NEEDS_MORE_EVIDENCE
            if evidence.liquidity is None
            else LimitStatus.PASS
        )
        return (
            _freshness_result(evidence.as_of, checked_now, max_age, evidence_refs),
            _session_result(evidence, config, evidence_refs),
            _calendar_result(evidence, config, evidence_refs),
            _spread_result(evidence, config.max_spread, evidence_refs),
            _result(
                "liquidity_availability",
                liquidity_status,
                evidence.liquidity,
                None,
                evidence_refs,
                4,
                reason=(
                    RiskErrorCode.MISSING_EVIDENCE
                    if liquidity_status is LimitStatus.NEEDS_MORE_EVIDENCE
                    else None
                ),
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        logger.error("Market-context Policy configuration is incomplete")
        raise RiskDomainError(
            RiskErrorCode.INVALID_RISK_CONFIG,
            "market-context policy configuration invalid",
        ) from error


__all__ = ["evaluate_market_context", "evaluate_portfolio_limits"]
