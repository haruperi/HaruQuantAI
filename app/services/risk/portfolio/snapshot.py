"""Deterministic portfolio risk snapshot construction from supplied evidence."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import ROUND_CEILING, Decimal

from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    LimitStatus,
    PortfolioRiskSnapshot,
    PortfolioState,
    RiskDomainError,
    RiskErrorCode,
)
from app.utils import logger

_MIN_SAMPLE_SIZE = 2


def _utc(value: datetime) -> datetime:
    """Require an aware UTC time.

    Args:
        value: Time to validate.

    Returns:
        Validated time.

    Raises:
        ValueError: If the time is not aware UTC.
    """
    logger.debug("Validating portfolio snapshot build time")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("snapshot build time must be aware UTC")
    return value


def _mean(values: Sequence[Decimal]) -> Decimal:
    """Calculate an exact Decimal arithmetic mean.

    Args:
        values: Non-empty values.

    Returns:
        Arithmetic mean.

    Raises:
        ValueError: If no values are supplied.
    """
    logger.debug("Calculating Decimal arithmetic mean")
    if not values:
        raise ValueError("mean requires at least one value")
    return sum(values, Decimal(0)) / Decimal(len(values))


def _sample_covariance(left: Sequence[Decimal], right: Sequence[Decimal]) -> Decimal:
    """Calculate aligned sample covariance with denominator n minus one.

    Args:
        left: First aligned series.
        right: Second aligned series.

    Returns:
        Sample covariance.

    Raises:
        ValueError: If series are unaligned or too short.
    """
    logger.debug("Calculating aligned Decimal sample covariance")
    if len(left) != len(right) or len(left) < _MIN_SAMPLE_SIZE:
        raise ValueError("covariance requires aligned samples")
    left_mean, right_mean = _mean(left), _mean(right)
    numerator = sum(
        ((left_item - left_mean) * (right_item - right_mean))
        for left_item, right_item in zip(left, right, strict=True)
    )
    return numerator / Decimal(len(left) - 1)


def _conversion_rates(state: PortfolioState) -> Mapping[str, Decimal]:
    """Build exact quote-to-base conversion rates.

    Args:
        state: Validated portfolio evidence.

    Returns:
        Currency-to-base rate mapping.
    """
    logger.debug("Indexing exact quote-to-base conversion evidence")
    base = state.account_snapshot.currency
    rates = {base: Decimal(1)}
    rates.update(
        {
            evidence.source_currency: evidence.composite_rate
            for evidence in state.fx_conversions
        }
    )
    return rates


def _signed_exposures(state: PortfolioState, config: RiskConfig) -> dict[str, Decimal]:
    """Calculate signed symbol exposure including governed pending orders.

    Args:
        state: Validated portfolio evidence.
        config: Active Risk policy.

    Returns:
        Signed base-currency exposure by symbol.

    Raises:
        RiskDomainError: If pending exposure is configured to block.
    """
    logger.info("Calculating pending-order-aware signed portfolio exposure")
    if (
        state.account_snapshot.orders
        and config.pending_order_exposure_policy == "block"
    ):
        raise RiskDomainError(
            RiskErrorCode.MISSING_EVIDENCE,
            "pending order exposure policy blocks snapshot",
        )
    rates = _conversion_rates(state)
    exposures: defaultdict[str, Decimal] = defaultdict(Decimal)
    for position in state.account_snapshot.positions:
        sign = Decimal(1) if position.side == "LONG" else Decimal(-1)
        exposures[position.symbol] += _item_exposure(
            state, rates, position.symbol, position.quantity, sign
        )
    for order in state.account_snapshot.orders:
        sign = Decimal(1) if order.side == "BUY" else Decimal(-1)
        exposures[order.symbol] += _item_exposure(
            state, rates, order.symbol, order.quantity, sign
        )
    return dict(exposures)


def _item_exposure(
    state: PortfolioState,
    rates: Mapping[str, Decimal],
    symbol: str,
    quantity: Decimal,
    sign: Decimal,
) -> Decimal:
    """Calculate one exact signed base-currency item exposure.

    Args:
        state: Validated portfolio evidence.
        rates: Quote-to-base rates.
        symbol: Referenced symbol.
        quantity: Remaining quantity.
        sign: Side sign.

    Returns:
        Signed base-currency exposure.
    """
    logger.debug("Calculating one signed base-currency exposure item")
    quote = state.symbol_quote_currencies[symbol]
    return (
        sign
        * quantity
        * state.symbol_prices[symbol]
        * state.symbol_contract_sizes[symbol]
        * rates[quote]
    )


def _dimension_exposures(
    state: PortfolioState, exposures: Mapping[str, Decimal]
) -> dict[str, Decimal]:
    """Aggregate absolute exposure across explicit dimensions.

    Args:
        state: Validated portfolio evidence.
        exposures: Signed exposure by symbol.

    Returns:
        Absolute exposure by canonical dimension key.
    """
    logger.debug("Aggregating absolute exposure dimensions")
    dimensions: defaultdict[str, Decimal] = defaultdict(Decimal)
    for symbol, exposure in exposures.items():
        absolute = abs(exposure)
        keys = {
            f"symbol:{symbol}",
            f"currency:{state.symbol_quote_currencies[symbol]}",
            *state.exposure_dimensions[symbol],
        }
        for key in keys:
            dimensions[key] += absolute
    return dict(sorted(dimensions.items()))


def _aligned_returns(
    state: PortfolioState,
    weights: Mapping[str, Decimal],
    lookback: int,
) -> tuple[dict[str, tuple[Decimal, ...]], tuple[Decimal, ...]]:
    """Select aligned returns and calculate signed portfolio returns.

    Args:
        state: Validated portfolio evidence.
        weights: Signed exposure weights.
        lookback: Maximum aligned observations.

    Returns:
        Selected symbol series and portfolio series.
    """
    logger.debug("Calculating aligned signed portfolio returns")
    selected = {
        symbol: tuple(state.return_history[symbol][-lookback:])
        for symbol in weights
        if symbol in state.return_history
    }
    if set(selected) != set(weights) or not selected:
        return selected, ()
    length = len(next(iter(selected.values())))
    portfolio = tuple(
        sum(
            (weights[symbol] * selected[symbol][index] for symbol in weights),
            Decimal(0),
        )
        for index in range(length)
    )
    return selected, portfolio


def _tail_metrics(
    portfolio_returns: Sequence[Decimal], equity: Decimal, confidence: Decimal
) -> tuple[Decimal, Decimal, Decimal]:
    """Calculate historical nearest-rank VaR, CVaR, and sample volatility.

    Args:
        portfolio_returns: Aligned portfolio returns.
        equity: Current account equity.
        confidence: Historical confidence ratio.

    Returns:
        Historical VaR, historical CVaR, and sample volatility.
    """
    logger.debug("Calculating historical portfolio tail-risk metrics")
    losses = sorted(-item * equity for item in portfolio_returns)
    rank = int(
        (confidence * Decimal(len(losses))).to_integral_value(rounding=ROUND_CEILING)
    )
    var = losses[max(0, rank - 1)]
    tail = tuple(loss for loss in losses if loss >= var)
    volatility = _sample_covariance(portfolio_returns, portfolio_returns).sqrt()
    return var, _mean(tail), volatility


def _risk_contributions(
    symbol_returns: Mapping[str, Sequence[Decimal]],
    portfolio_returns: Sequence[Decimal],
    weights: Mapping[str, Decimal],
) -> dict[str, Decimal]:
    """Calculate covariance-based symbol risk contributions.

    Args:
        symbol_returns: Aligned per-symbol return series.
        portfolio_returns: Aligned portfolio return series.
        weights: Signed exposure weights.

    Returns:
        Contribution by symbol, or an empty mapping for zero variance.
    """
    logger.debug("Calculating covariance-based portfolio risk contributions")
    variance = _sample_covariance(portfolio_returns, portfolio_returns)
    if variance <= 0:
        return {}
    return {
        symbol: weights[symbol]
        * _sample_covariance(returns, portfolio_returns)
        / variance
        for symbol, returns in symbol_returns.items()
    }


def _correlation_metric(
    state: PortfolioState, symbols: Sequence[str]
) -> Decimal | None:
    """Validate the O(n²) PSD certificate and return maximum correlation.

    Args:
        state: Validated portfolio evidence.
        symbols: Symbols with active exposure.

    Returns:
        Maximum absolute pair correlation, or None when unavailable.

    Raises:
        RiskDomainError: If complete correlation evidence lacks the V1 PSD certificate.
    """
    logger.debug("Certifying supplied correlation evidence in quadratic time")
    ordered = tuple(sorted(symbols))
    if len(ordered) < _MIN_SAMPLE_SIZE:
        return Decimal(0)
    pairs = {
        f"{left}|{right}"
        for index, left in enumerate(ordered)
        for right in ordered[index + 1 :]
    }
    if not pairs.issubset(state.correlations):
        return None
    for symbol in ordered:
        row_sum = sum(
            (
                abs(state.correlations[f"{min(symbol, other)}|{max(symbol, other)}"])
                for other in ordered
                if other != symbol
            ),
            Decimal(0),
        )
        if row_sum > 1:
            raise RiskDomainError(
                RiskErrorCode.INVALID_PORTFOLIO_STATE,
                "correlation matrix lacks V1 PSD certificate",
            )
    return max(abs(state.correlations[pair]) for pair in pairs)


def _validate_build_inputs(
    state: PortfolioState, config: RiskConfig, now: datetime
) -> datetime:
    """Validate snapshot freshness and required configuration bindings.

    Args:
        state: Portfolio evidence.
        config: Active Risk configuration.
        now: Injected current time.

    Returns:
        Validated current time.

    Raises:
        RiskDomainError: If evidence is stale or required policy is absent.
    """
    logger.info("Validating portfolio snapshot inputs and freshness")
    try:
        checked_now = _utc(now)
    except ValueError as error:
        raise RiskDomainError(
            RiskErrorCode.INVALID_PORTFOLIO_STATE, "invalid snapshot time"
        ) from error
    max_age = config.evidence_max_age_seconds.get("portfolio")
    if max_age is None:
        raise RiskDomainError(
            RiskErrorCode.MISSING_EVIDENCE, "portfolio freshness policy missing"
        )
    skew = config.clock_skew_tolerance_seconds or Decimal(0)
    age = Decimal(str((checked_now - state.as_of).total_seconds()))
    if checked_now > state.expires_at or age > Decimal(max_age) or age < -skew:
        raise RiskDomainError(
            RiskErrorCode.MISSING_EVIDENCE, "portfolio evidence stale"
        )
    return checked_now


def _build_snapshot(
    state: PortfolioState, config: RiskConfig, now: datetime
) -> PortfolioRiskSnapshot:
    """Build the canonical snapshot after boundary validation.

    Args:
        state: Validated portfolio evidence.
        config: Active Risk policy.
        now: Validated build time.

    Returns:
        Immutable canonical snapshot.
    """
    logger.info("Building canonical portfolio risk snapshot")
    exposures = _signed_exposures(state, config)
    gross = sum((abs(value) for value in exposures.values()), Decimal(0))
    net = sum(exposures.values(), Decimal(0))
    equity = state.account_snapshot.equity
    weights = (
        {symbol: exposure / gross for symbol, exposure in exposures.items()}
        if gross > 0
        else {}
    )
    gaps: list[str] = list(state.missing_fields)
    assumptions = [
        f"pending_order_exposure_policy={config.pending_order_exposure_policy}",
        "historical_var_nearest_rank",
        "aligned_returns",
    ]
    historical_var: Decimal | None = None
    historical_cvar: Decimal | None = None
    volatility: Decimal | None = None
    contributions: dict[str, Decimal] = {}
    returns_coverage = "missing"
    if config.var_lookback is None:
        gaps.append("var_lookback")
    elif weights:
        assumptions.append(f"var_lookback={config.var_lookback}")
        selected, portfolio_returns = _aligned_returns(
            state, weights, config.var_lookback
        )
        minimum = config.var_min_observations or _MIN_SAMPLE_SIZE
        if len(portfolio_returns) >= minimum:
            historical_var, historical_cvar, volatility = _tail_metrics(
                portfolio_returns, equity, config.var_confidence
            )
            contributions = _risk_contributions(selected, portfolio_returns, weights)
            if not contributions:
                gaps.append("risk_contributions")
            returns_coverage = "complete"
        else:
            gaps.append("return_history")
            returns_coverage = "partial" if portfolio_returns else "missing"
    correlation = _correlation_metric(state, tuple(exposures))
    if correlation is None:
        gaps.append("correlations")
    correlation_status = (
        LimitStatus.NEEDS_MORE_EVIDENCE
        if correlation is None
        else LimitStatus.FAIL
        if correlation > config.max_correlation
        else LimitStatus.PASS
    )
    config_hash = compute_config_hash(config)
    snapshot_key = (
        f"{state.account_snapshot.account_id}|{state.as_of.isoformat()}|{config_hash}"
    )
    return PortfolioRiskSnapshot(
        snapshot_id=hashlib.sha256(snapshot_key.encode("utf-8")).hexdigest(),
        account_id=state.account_snapshot.account_id,
        base_currency=state.account_snapshot.currency,
        equity=equity,
        daily_loss=max(Decimal(0), state.day_start_equity - equity),
        total_loss=max(Decimal(0), state.inception_equity - equity),
        gross_exposure=gross,
        net_exposure=net,
        drawdown=(
            max(Decimal(0), state.peak_equity - equity) / state.peak_equity
            if state.peak_equity > 0
            else Decimal(0)
        ),
        margin_utilization=(
            state.account_snapshot.margin_used / equity
            if state.account_snapshot.margin_used is not None and equity > 0
            else None
        ),
        effective_leverage=gross / equity if equity > 0 else None,
        historical_var=historical_var,
        historical_cvar=historical_cvar,
        volatility=volatility,
        portfolio_correlation=correlation,
        exposure_by_dimension=_dimension_exposures(state, exposures),
        contributions=contributions,
        limit_statuses={"correlation": correlation_status},
        assumptions=tuple(assumptions),
        coverage={
            "account": "complete",
            "valuation": "complete",
            "fx": "complete",
            "returns": returns_coverage,
            "correlations": "complete" if correlation is not None else "missing",
        },
        gaps=tuple(dict.fromkeys(gaps)),
        regime=None,
        as_of=now,
        config_hash=config_hash,
        evidence_refs={
            "account": state.account_snapshot.request_id,
            **{
                f"fx:{item.source_currency}": item.request_id
                for item in state.fx_conversions
            },
        },
        request_id=state.request_id,
        workflow_id=state.workflow_id,
    )


def build_portfolio_risk_snapshot(
    state: PortfolioState, config: RiskConfig, *, now: datetime
) -> PortfolioRiskSnapshot:
    """Build an immutable pending-order-aware portfolio Risk snapshot.

    Args:
        state: Complete supplied portfolio evidence.
        config: Active validated Risk configuration.
        now: Injected current UTC time.

    Returns:
        Reproducible canonical portfolio Risk snapshot.

    Raises:
        RiskDomainError: If evidence is invalid, missing, stale, or calculation fails.
    """
    logger.info("Starting deterministic portfolio risk snapshot build")
    checked_now = _validate_build_inputs(state, config, now)
    try:
        return _build_snapshot(state, config, checked_now)
    except RiskDomainError:
        logger.error("Portfolio snapshot build failed with a coded Risk error")
        raise
    except (ArithmeticError, KeyError, ValueError) as error:
        logger.error("Portfolio snapshot calculation failed closed")
        raise RiskDomainError(
            RiskErrorCode.SNAPSHOT_BUILD_FAILED,
            "portfolio snapshot calculation failed",
        ) from error


__all__ = ["build_portfolio_risk_snapshot"]
