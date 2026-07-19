"""Deterministic supplied-evidence Risk regime classification and tightening."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    PortfolioRiskSnapshot,
    RegimeAssessment,
    RiskDomainError,
    RiskErrorCode,
    validate_market_context_evidence,
)
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.data.contracts import MarketContextEvidence

_State = Literal["normal", "elevated", "high", "unknown"]
_DIMENSIONS = (
    "volatility",
    "liquidity",
    "correlation",
    "drawdown",
    "crisis",
    "news",
    "session",
)


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If the timestamp is not aware UTC.
    """
    logger.debug("Validating regime assessment UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("regime assessment time must be aware UTC")
    return value


def _metric_state(value: Decimal | None, elevated: Decimal, high: Decimal) -> _State:
    """Classify one optional higher-is-riskier metric.

    Args:
        value: Supplied metric or None.
        elevated: Elevated-state threshold.
        high: High-state threshold.

    Returns:
        Deterministic regime state.
    """
    logger.debug("Classifying one numeric Risk regime metric")
    if value is None:
        return "unknown"
    if value >= high:
        return "high"
    if value >= elevated:
        return "elevated"
    return "normal"


def _maximum(values: tuple[Decimal | None, ...]) -> Decimal | None:
    """Return the maximum supplied metric or None.

    Args:
        values: Optional metrics.

    Returns:
        Maximum non-None value.
    """
    logger.debug("Selecting maximum supplied regime metric")
    present = tuple(value for value in values if value is not None)
    return max(present) if present else None


def _crisis_state(
    evidence: MarketContextEvidence, config: RiskConfig, now: datetime
) -> _State:
    """Classify supplied flags and configured current crisis windows.

    Args:
        evidence: Supplied market context.
        config: Active Risk policy.
        now: Checked evaluation time.

    Returns:
        Normal or high crisis state.
    """
    logger.debug("Classifying supplied crisis regime evidence")
    in_window = any(
        start <= now <= end for start, end in config.crisis_windows_utc.values()
    )
    return "high" if evidence.crisis_flags or in_window else "normal"


def _context_states(
    evidence: MarketContextEvidence, config: RiskConfig, now: datetime
) -> dict[str, _State]:
    """Classify liquidity, crisis, news, and session context.

    Args:
        evidence: Supplied market context.
        config: Active Risk policy.
        now: Checked evaluation time.

    Returns:
        Four deterministic context states.
    """
    logger.debug("Classifying normalized market-context regime states")
    liquidity: _State
    if evidence.liquidity is None:
        liquidity = "unknown"
    elif evidence.liquidity == 0:
        liquidity = "high"
    else:
        liquidity = "normal"
    news: _State
    if evidence.calendar_state is None or evidence.calendar_state == "unknown":
        news = "unknown"
    elif evidence.calendar_state in config.blocked_calendar_states:
        news = "high"
    else:
        news = "normal"
    session: _State
    if evidence.session_state is None or evidence.session_state == "unknown":
        session = "unknown"
    elif evidence.session_state in config.allowed_session_states:
        session = "normal"
    else:
        session = "high"
    return {
        "liquidity": liquidity,
        "crisis": _crisis_state(evidence, config, now),
        "news": news,
        "session": session,
    }


def _enabled_states(
    snapshot: PortfolioRiskSnapshot,
    evidence: MarketContextEvidence,
    config: RiskConfig,
    now: datetime,
) -> dict[str, _State]:
    """Classify every enabled V1 regime dimension.

    Args:
        snapshot: Immutable portfolio Risk measurements.
        evidence: Supplied market context.
        config: Active Risk policy.
        now: Checked evaluation time.

    Returns:
        Complete classified dimension mapping.
    """
    logger.debug("Classifying all enabled Risk regime dimensions")
    thresholds = config.regime_thresholds
    market_correlation = (
        max((abs(value) for value in evidence.correlations.values()), default=None)
        if evidence.correlations
        else None
    )
    states: dict[str, _State] = {
        "volatility": _metric_state(
            _maximum((snapshot.volatility, evidence.volatility)),
            thresholds["volatility_elevated"],
            thresholds["volatility_high"],
        ),
        "correlation": _metric_state(
            _maximum((snapshot.portfolio_correlation, market_correlation)),
            thresholds["correlation_elevated"],
            thresholds["correlation_high"],
        ),
        "drawdown": _metric_state(
            snapshot.drawdown,
            thresholds["drawdown_elevated"],
            thresholds["drawdown_high"],
        ),
    }
    states.update(_context_states(evidence, config, now))
    return states


def _assessment_id(
    snapshot: PortfolioRiskSnapshot,
    evidence: MarketContextEvidence,
    config_hash: str,
    states: dict[str, _State],
    now: datetime,
) -> str:
    """Derive the deterministic regime assessment identity.

    Args:
        snapshot: Source snapshot.
        evidence: Source market context.
        config_hash: Active configuration hash.
        states: Classified states.
        now: Assessment time.

    Returns:
        Lowercase SHA-256 identity.
    """
    logger.debug("Deriving deterministic regime assessment identity")
    material = {
        "snapshot_id": snapshot.snapshot_id,
        "market_request_id": evidence.request_id,
        "config_hash": config_hash,
        "states": states,
        "assessed_at": now.isoformat(),
    }
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def _validate_freshness(
    snapshot: PortfolioRiskSnapshot, config: RiskConfig, now: datetime
) -> None:
    """Validate deterministic snapshot age for regime use.

    Args:
        snapshot: Source snapshot.
        config: Active Risk policy.
        now: Checked evaluation time.

    Raises:
        RiskDomainError: If snapshot time is future or stale.
    """
    logger.debug("Validating snapshot freshness for regime assessment")
    try:
        max_age = config.evidence_max_age_seconds["portfolio"]
    except KeyError as error:
        raise RiskDomainError(
            RiskErrorCode.MISSING_EVIDENCE,
            "portfolio freshness policy missing",
        ) from error
    age = (now - snapshot.as_of).total_seconds()
    if age < 0 or age > max_age:
        raise RiskDomainError(
            RiskErrorCode.STALE_EVIDENCE,
            "portfolio snapshot is stale for regime assessment",
        )


def _require_live_evidence(config: RiskConfig, missing: tuple[str, ...]) -> None:
    """Fail closed when a live assessment has unknown dimensions.

    Args:
        config: Active Risk policy.
        missing: Unknown regime dimensions.

    Raises:
        RiskDomainError: If live evidence is incomplete.
    """
    logger.debug("Checking required live regime evidence")
    if config.profile == "live" and missing:
        raise RiskDomainError(
            RiskErrorCode.MISSING_EVIDENCE,
            "live regime evidence is incomplete",
        )


def assess_risk_regime(
    snapshot: PortfolioRiskSnapshot,
    evidence: MarketContextEvidence,
    config: RiskConfig,
    *,
    now: datetime,
) -> RegimeAssessment:
    """Classify supplied Risk context and return only tightening modifiers.

    Args:
        snapshot: Immutable portfolio Risk measurements.
        evidence: Data-owned immutable market context.
        config: Active validated Risk policy.
        now: Injected current UTC time.

    Returns:
        Deterministic classified regime assessment.

    Raises:
        RiskDomainError: If required evidence is missing, stale, or invalid.
    """
    logger.info("Assessing deterministic supplied-evidence Risk regime")
    try:
        checked_now = _utc(now)
        validate_market_context_evidence(evidence, now=checked_now)
        _validate_freshness(snapshot, config, checked_now)
        config_hash = compute_config_hash(config)
        if config.regime_assessment_enabled:
            states = _enabled_states(snapshot, evidence, config, checked_now)
            missing = tuple(
                dimension for dimension in _DIMENSIONS if states[dimension] == "unknown"
            )
            _require_live_evidence(config, missing)
            modifiers = {
                dimension: config.regime_modifiers[state]
                for dimension, state in states.items()
                if state in {"elevated", "high"}
            }
        else:
            states = dict.fromkeys(_DIMENSIONS, "unknown")
            missing = ("assessment_disabled",)
            modifiers = {}
        previous = dict.fromkeys(_DIMENSIONS, "unknown")
        transitions = tuple(
            f"{dimension}:unknown->{states[dimension]}"
            for dimension in _DIMENSIONS
            if states[dimension] != "unknown"
        )
        return RegimeAssessment(
            assessment_id=_assessment_id(
                snapshot, evidence, config_hash, states, checked_now
            ),
            states=states,
            previous_states=previous,
            transitions=transitions,
            modifiers=modifiers,
            evidence_refs=(
                snapshot.snapshot_id,
                evidence.request_id,
                *snapshot.evidence_refs.values(),
            ),
            missing_fields=missing,
            assessed_at=checked_now,
        )
    except RiskDomainError:
        logger.error("Risk regime assessment failed closed")
        raise
    except (ArithmeticError, KeyError, TypeError, ValueError) as error:
        logger.error("Risk regime classification failed")
        raise RiskDomainError(
            RiskErrorCode.CALCULATION_FAILED,
            "regime assessment calculation failed",
        ) from error


__all__ = ["assess_risk_regime"]
