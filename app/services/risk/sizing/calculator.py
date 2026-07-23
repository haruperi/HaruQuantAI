"""Migration-evidenced deterministic position sizing recommendations."""

from decimal import ROUND_FLOOR, Decimal

from app.services.risk.config import RiskConfig  # noqa: TC001
from app.services.risk.contracts import (
    PortfolioRiskSnapshot,
    PositionSizingRequest,
    PositionSizingResult,
    RiskDomainError,
    RiskErrorCode,
)
from app.utils import logger


def _risk_per_unit(
    stop_distance: Decimal | None, unit_value: Decimal | None
) -> Decimal:
    """Calculate explicit account-currency risk per size unit.

    Args:
        stop_distance: Price-space stop distance.
        unit_value: Account-currency value per price unit and size unit.

    Returns:
        Positive risk per size unit.

    Raises:
        RiskDomainError: If stop evidence is missing or invalid.
    """
    logger.debug("Calculating explicit risk per position-size unit")
    if stop_distance is None or stop_distance <= 0:
        raise RiskDomainError(RiskErrorCode.MISSING_STOP_LOSS, "stop distance missing")
    if unit_value is None or unit_value <= 0:
        raise RiskDomainError(RiskErrorCode.CALCULATION_FAILED, "unit value invalid")
    return stop_distance * unit_value


def _fixed_risk_raw(request: PositionSizingRequest) -> Decimal:
    """Calculate explicit monetary fixed-risk size.

    Args:
        request: Complete sizing request.

    Returns:
        Raw size.

    Raises:
        RiskDomainError: If monetary risk is absent.
    """
    logger.debug("Calculating fixed monetary risk size")
    if request.risk_amount is None or request.risk_amount <= 0:
        raise RiskDomainError(RiskErrorCode.CALCULATION_FAILED, "risk amount missing")
    return request.risk_amount / _risk_per_unit(
        request.stop_distance, request.unit_value
    )


def _fixed_fractional_raw(
    request: PositionSizingRequest, snapshot: PortfolioRiskSnapshot
) -> Decimal:
    """Calculate fixed-fractional equity size.

    Args:
        request: Complete sizing request.
        snapshot: Current portfolio snapshot.

    Returns:
        Raw size.

    Raises:
        RiskDomainError: If fraction or equity is invalid.
    """
    logger.debug("Calculating fixed-fractional equity size")
    if request.risk_fraction is None or not Decimal(0) < request.risk_fraction <= 1:
        raise RiskDomainError(RiskErrorCode.CALCULATION_FAILED, "risk fraction invalid")
    if snapshot.equity <= 0:
        raise RiskDomainError(RiskErrorCode.CALCULATION_FAILED, "equity invalid")
    return (
        snapshot.equity
        * request.risk_fraction
        / _risk_per_unit(request.stop_distance, request.unit_value)
    )


def _kelly_raw(
    request: PositionSizingRequest,
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
) -> tuple[Decimal, bool, str | None]:
    """Calculate fractional-Kelly size or its explicit fixed-risk fallback.

    Args:
        request: Complete Kelly evidence.
        snapshot: Current portfolio snapshot.
        config: Active Kelly policy.

    Returns:
        Raw size, fallback flag, and fallback reason.

    Raises:
        RiskDomainError: If policy or evidence is insufficient.
    """
    logger.debug("Calculating migration-evidenced fractional-Kelly size")
    if request.trade_count is None or request.trade_count < config.min_kelly_trades:
        if config.kelly_insufficient_evidence_mode != "fixed_risk_fallback":
            raise RiskDomainError(
                RiskErrorCode.INSUFFICIENT_K_EVIDENCE,
                "Kelly trade evidence insufficient",
            )
        raw = _fixed_risk_raw(request)
        return raw, True, "insufficient_k_evidence"
    if (
        request.win_rate is None
        or request.payoff_ratio is None
        or request.payoff_ratio <= 0
        or config.fractional_kelly_multiplier is None
    ):
        raise RiskDomainError(
            RiskErrorCode.INSUFFICIENT_K_EVIDENCE, "Kelly evidence incomplete"
        )
    full_kelly = max(
        Decimal(0),
        request.win_rate - (Decimal(1) - request.win_rate) / request.payoff_ratio,
    )
    if (
        full_kelly > 0
        and config.fractional_kelly_multiplier == 1
        and not config.allow_full_kelly
    ):
        raise RiskDomainError(
            RiskErrorCode.CALCULATION_FAILED, "full Kelly is not approved"
        )
    applied = full_kelly * config.fractional_kelly_multiplier
    return (
        snapshot.equity
        * applied
        / _risk_per_unit(request.stop_distance, request.unit_value),
        False,
        None,
    )


def _volatility_raw(
    request: PositionSizingRequest, snapshot: PortfolioRiskSnapshot
) -> Decimal:
    """Calculate volatility-stop-adjusted fractional size.

    Args:
        request: Complete volatility sizing evidence.
        snapshot: Current portfolio snapshot.

    Returns:
        Raw size.

    Raises:
        RiskDomainError: If volatility evidence is absent or invalid.
    """
    logger.debug("Calculating volatility-stop-adjusted size")
    if (
        request.asset_volatility is None
        or request.volatility_multiplier is None
        or request.asset_volatility <= 0
        or request.volatility_multiplier <= 0
        or request.risk_fraction is None
        or request.unit_value is None
    ):
        raise RiskDomainError(
            RiskErrorCode.INSUFFICIENT_VOLATILITY_EVIDENCE,
            "volatility sizing evidence incomplete",
        )
    stop = request.asset_volatility * request.volatility_multiplier
    if not Decimal(0) < request.risk_fraction <= 1 or snapshot.equity <= 0:
        raise RiskDomainError(
            RiskErrorCode.INSUFFICIENT_VOLATILITY_EVIDENCE,
            "volatility risk fraction or equity invalid",
        )
    return snapshot.equity * request.risk_fraction / (stop * request.unit_value)


def _raw_size(
    request: PositionSizingRequest,
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
) -> tuple[Decimal, bool, str | None]:
    """Route one strict request to its retained formula.

    Args:
        request: Complete sizing request.
        snapshot: Current portfolio snapshot.
        config: Active sizing policy.

    Returns:
        Raw size, fallback flag, and fallback reason.

    Raises:
        RiskDomainError: If method evidence is invalid.
    """
    logger.info("Applying approved sizing formula: %s", request.method)
    if request.method == "fixed_lot":
        if request.fixed_lot is None:
            raise RiskDomainError(RiskErrorCode.CALCULATION_FAILED, "fixed lot missing")
        return request.fixed_lot, False, None
    if request.method == "fixed_risk":
        return _fixed_risk_raw(request), False, None
    if request.method == "fixed_fractional":
        return _fixed_fractional_raw(request, snapshot), False, None
    if request.method == "milestone":
        if request.fixed_lot is None or request.milestone_multiplier is None:
            raise RiskDomainError(
                RiskErrorCode.CALCULATION_FAILED, "milestone evidence missing"
            )
        return request.fixed_lot * request.milestone_multiplier, False, None
    if request.method == "fractional_kelly":
        return _kelly_raw(request, snapshot, config)
    if request.method == "volatility":
        return _volatility_raw(request, snapshot), False, None
    raise RiskDomainError(RiskErrorCode.CALCULATION_FAILED, "sizing method invalid")


def _apply_correlation_penalty(
    raw_size: Decimal,
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    constraints: list[str],
) -> tuple[Decimal, Decimal | None]:
    """Apply an explicit configured correlation penalty when breached.

    Args:
        raw_size: Raw formula output.
        snapshot: Current portfolio snapshot.
        config: Active correlation policy.
        constraints: Mutable local disclosure list.

    Returns:
        Adjusted size and applied multiplier.

    Raises:
        RiskDomainError: If configured adjustment lacks correlation evidence.
    """
    logger.debug("Evaluating configured correlation sizing penalty")
    penalty = config.correlation_size_penalty
    if penalty is None:
        return raw_size, None
    if snapshot.portfolio_correlation is None:
        raise RiskDomainError(
            RiskErrorCode.MISSING_EVIDENCE, "portfolio correlation missing"
        )
    if snapshot.portfolio_correlation > config.max_correlation:
        constraints.append("correlation_size_penalty")
        return raw_size * penalty, penalty
    return raw_size, None


def _normalize(
    raw_size: Decimal, request: PositionSizingRequest, constraints: list[str]
) -> Decimal:
    """Cap and floor size to exact broker constraints.

    Args:
        raw_size: Non-negative raw size.
        request: Broker size constraints.
        constraints: Mutable local disclosure list.

    Returns:
        Exact normalized size, possibly zero.
    """
    logger.debug("Normalizing size to migrated broker-step behavior")
    capped = raw_size
    if capped > request.broker_max_size:
        capped = request.broker_max_size
        constraints.append("broker_maximum_cap")
    steps = (capped / request.broker_size_step).to_integral_value(rounding=ROUND_FLOOR)
    normalized = steps * request.broker_size_step
    if normalized != capped:
        constraints.append("broker_step_floor")
    if normalized < request.broker_min_size:
        constraints.append("below_broker_minimum")
        return Decimal(0)
    return normalized


def _validate_raw_size(raw_size: Decimal) -> Decimal:
    """Require a finite non-negative raw sizing result.

    Args:
        raw_size: Formula output.

    Returns:
        Validated raw size.

    Raises:
        RiskDomainError: If the raw size is non-finite or negative.
    """
    logger.debug("Validating raw position-size formula output")
    if not raw_size.is_finite() or raw_size < 0:
        raise RiskDomainError(RiskErrorCode.CALCULATION_FAILED, "raw size is invalid")
    return raw_size


def calculate_position_size(
    request: PositionSizingRequest,
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
) -> PositionSizingResult:
    """Calculate one deterministic non-authorizing position-size recommendation.

    Args:
        request: Complete method and broker evidence.
        snapshot: Current immutable portfolio Risk snapshot.
        config: Active immutable Risk policy.

    Returns:
        Exact normalized sizing recommendation.

    Raises:
        RiskDomainError: If required stop, statistical, volatility, or policy
            evidence is absent or calculation fails.
    """
    logger.info("Calculating deterministic position-size recommendation")
    try:
        raw, fallback_used, fallback_reason = _raw_size(request, snapshot, config)
        raw = _validate_raw_size(raw)
        constraints: list[str] = []
        adjusted, correlation_adjustment = _apply_correlation_penalty(
            raw, snapshot, config, constraints
        )
        normalized = _normalize(adjusted, request, constraints)
        return PositionSizingResult(
            method=request.method,
            requested_size=request.requested_size,
            calculated_size=raw,
            normalized_size=normalized,
            constraints_applied=tuple(constraints),
            evidence_gaps=(),
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            correlation_adjustment=correlation_adjustment,
        )
    except RiskDomainError:
        logger.error("Position sizing failed with a coded Risk error")
        raise
    except (ArithmeticError, ValueError) as error:
        logger.error("Position sizing calculation failed closed")
        raise RiskDomainError(
            RiskErrorCode.CALCULATION_FAILED, "position sizing failed"
        ) from error


__all__ = ["calculate_position_size"]
