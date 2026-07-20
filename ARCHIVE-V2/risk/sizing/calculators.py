"""Position sizing calculator engines.

Provides stateless pure calculators and backward-compatible sizers
conforming to broker step limitations and risk policy constraints.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.services.risk.models.contracts import (
    PositionSizingRequest,
    PositionSizingResult,
)
from app.services.risk.sizing.contracts import (
    AdvisorySizingResult,
    CorrelationImpact,
    KellyEvidence,
    RiskMilestone,
    SizingMethod,
    SymbolRiskMetadata,
)
from app.services.risk.sizing.normalization import (
    normalize_volume,
    validate_normalized_volume,
    validate_symbol_volume_metadata,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.risk.models import PortfolioState, RiskConfig


def _pre_validate_inputs(
    symbol_metadata: SymbolRiskMetadata,
    portfolio_equity: Decimal,
    sizing_method: str,
) -> PositionSizingResult | None:
    """Pre-validate metadata and equity to reduce return statement complexity."""
    meta_val = validate_symbol_volume_metadata(symbol_metadata)
    if not meta_val["valid"]:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=sizing_method,
            constraints_applied=["missing_symbol_metadata"],
            risk_contribution=Decimal("0.0"),
        )

    if symbol_metadata.conversion_rate <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=sizing_method,
            constraints_applied=["invalid_conversion_rate"],
            risk_contribution=Decimal("0.0"),
        )

    if portfolio_equity <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=sizing_method,
            constraints_applied=["zero_or_negative_equity"],
            risk_contribution=Decimal("0.0"),
        )
    return None


# =====================================================================
# V2 Pure Calculators
# =====================================================================


def calculate_stop_distance(
    request: PositionSizingRequest,
    symbol_metadata: SymbolRiskMetadata,
    market_context: dict[str, Any] | None = None,
) -> Decimal:
    """Calculate price stop distance using request attributes or volatility checks.

    Args:
        request: PositionSizingRequest containing parameters.
        symbol_metadata: Symbol spec metadata.
        market_context: Optional context dictionary for volatility.

    Returns:
        Decimal: Stop distance in price space.
    """
    logger.debug("Calculating stop distance for %s", request.symbol)
    ctx = market_context or {}

    if request.method == SizingMethod.VOLATILITY_ADJUSTED.value:
        m1_vol = ctx.get("m1_volatility")
        multiplier = request.multiplier or Decimal("2.0")

        if m1_vol is not None:
            stop_price = Decimal(str(m1_vol)) * multiplier
        elif request.atr_value is not None:
            stop_price = request.atr_value * multiplier
        else:
            raise ValueError("Missing volatility inputs.")
    elif request.stop_loss_pips is not None:
        stop_pips = Decimal(str(request.stop_loss_pips))
        pip_size = (
            Decimal("0.01") if symbol_metadata.digits in {2, 3} else Decimal("0.0001")
        )
        stop_price = stop_pips * pip_size
    else:
        stop_price = Decimal("0.0")

    return stop_price


def convert_stop_distance_to_account_risk(
    distance: Decimal,
    symbol: SymbolRiskMetadata,
    account_currency: str,
) -> Decimal:
    """Convert price stop distance into account-currency risk per lot.

    Args:
        distance: Price distance to convert.
        symbol: Symbol metadata holding specs.
        account_currency: Target account currency Leg.

    Returns:
        Decimal: Per-lot risk in account currency.
    """
    logger.debug(
        "Converting stop distance %s to account risk for %s in %s",
        distance,
        symbol.symbol,
        account_currency,
    )
    _ = account_currency

    tick_size = symbol.tick_size
    if tick_size is None or tick_size <= 0:
        tick_size = Decimal(10) ** -symbol.digits

    tick_value = symbol.tick_value
    if tick_value is None or tick_value <= 0:
        tick_value = tick_size * symbol.contract_size * symbol.conversion_rate

    if distance <= 0 or tick_size <= 0:
        return Decimal("0.0")

    risk_per_lot = (distance / tick_size) * tick_value
    return risk_per_lot


def _apply_reductions_v2(
    raw_size: Decimal,
    drawdown_step_down_multiplier: Decimal,
    currency_exposure_reduction: Decimal,
    correlation_cluster_reduction: Decimal,
    constraints: list[str],
) -> Decimal:
    """Apply risk mitigation multipliers to raw lot size.

    Args:
        raw_size: Pre-reduction lot size.
        drawdown_step_down_multiplier: Step-down multiplier.
        currency_exposure_reduction: Currency exposure reduction.
        correlation_cluster_reduction: Correlation cluster reduction.
        constraints: Constraints tracking list.

    Returns:
        Decimal: Reduced lot size.
    """
    size = raw_size
    if drawdown_step_down_multiplier < 1:
        size *= drawdown_step_down_multiplier
        constraints.append("drawdown_step_down")
    if currency_exposure_reduction < 1:
        size *= currency_exposure_reduction
        constraints.append("currency_exposure_reduction")
    if correlation_cluster_reduction < 1:
        size *= correlation_cluster_reduction
        constraints.append("correlation_cluster_reduction")
    return size


def _build_final_sizing_result(
    raw_size: Decimal,
    stop_distance_price: Decimal,
    stop_pips: Decimal,
    symbol_metadata: SymbolRiskMetadata,
    sizing_method: str,
    constraints: list[str],
) -> PositionSizingResult:
    """Consolidates raw sizing through broker validations to return target result.

    Args:
        raw_size: Calculated lot size after reductions/caps.
        stop_distance_price: Distance in price space.
        stop_pips: Distance in pips.
        symbol_metadata: Broker spec bounds.
        sizing_method: Selected method identifier.
        constraints: Tracking constraints names.

    Returns:
        PositionSizingResult: Validated positioning outcome.
    """
    logger.debug("Building final sizing result for raw size %s", raw_size)

    # 1. Round to broker lot step
    normalized = normalize_volume(raw_size, symbol_metadata)

    # 2. Check bounds
    val_res = validate_normalized_volume(normalized, symbol_metadata)
    if not val_res["valid"]:
        details = val_res.get("details", {})
        if details.get("under_min"):
            # Too small -> zero volume rejection
            constraints.append("below_minimum_volume")
            return PositionSizingResult(
                calculated_volume=Decimal("0.0"),
                stop_distance_pips=stop_pips,
                sizing_method=sizing_method,
                constraints_applied=sorted(constraints),
                risk_contribution=Decimal("0.0"),
            )
        if details.get("over_max"):
            # Too large -> cap at maximum
            normalized = symbol_metadata.volume_max
            constraints.append("volume_max_cap")

    # 3. Calculate risk contribution
    risk_per_lot = convert_stop_distance_to_account_risk(
        stop_distance_price, symbol_metadata, "USD"
    )
    if risk_per_lot <= 0:
        risk_per_lot = symbol_metadata.contract_size * symbol_metadata.conversion_rate

    risk_contribution = normalized * risk_per_lot

    return PositionSizingResult(
        calculated_volume=normalized,
        stop_distance_pips=stop_pips,
        sizing_method=sizing_method,
        constraints_applied=sorted(constraints),
        risk_contribution=risk_contribution,
    )


def calculate_fixed_risk_size(
    request: PositionSizingRequest,
    portfolio_equity: Decimal,
    symbol_metadata: SymbolRiskMetadata,
    config: RiskConfig,
    drawdown_step_down_multiplier: Decimal = Decimal("1.0"),
    currency_exposure_reduction: Decimal = Decimal("1.0"),
    correlation_cluster_reduction: Decimal = Decimal("1.0"),
    market_context: dict[str, Any] | None = None,
) -> PositionSizingResult:
    """Pure calculator sizing position from fixed monetary bounds.

    Args:
        request: Sizing request settings.
        portfolio_equity: Portfolio equity balance.
        symbol_metadata: Symbol spec bounds.
        config: Active risk configuration.
        drawdown_step_down_multiplier: Mitigation drawdown factor.
        currency_exposure_reduction: Currency exposure reduction.
        correlation_cluster_reduction: Correlation cluster reduction.
        market_context: Optional context parameters.

    Returns:
        PositionSizingResult: Sizing outcome.
    """
    logger.info("Stateless calculate_fixed_risk_size called.")
    ctx = market_context or {}
    constraints: list[str] = []

    # 1. Spec validation
    err_res = _pre_validate_inputs(
        symbol_metadata, portfolio_equity, SizingMethod.FIXED_RISK.value
    )
    if err_res is not None:
        return err_res

    # 2. Stop distance calculation
    try:
        stop_price = calculate_stop_distance(request, symbol_metadata, ctx)
    except ValueError:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.FIXED_RISK.value,
            constraints_applied=["missing_volatility_inputs"],
            risk_contribution=Decimal("0.0"),
        )

    if stop_price <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.FIXED_RISK.value,
            constraints_applied=["invalid_stop_distance"],
            risk_contribution=Decimal("0.0"),
        )

    # 3. Risk amount calculation
    max_risk_pct = getattr(config, "max_risk_per_trade", Decimal("0.02"))
    max_risk_amt = portfolio_equity * max_risk_pct

    if request.risk_amount is not None:
        risk_amount = Decimal(str(request.risk_amount))
    elif request.risk_percent is not None:
        risk_amount = portfolio_equity * Decimal(str(request.risk_percent))
    else:
        risk_amount = max_risk_amt

    if risk_amount > max_risk_amt:
        risk_amount = max_risk_amt
        constraints.append("max_risk_per_trade_cap")

    # 4. Convert stop distance to risk per lot
    risk_per_lot = convert_stop_distance_to_account_risk(
        stop_price, symbol_metadata, "USD"
    )
    if risk_per_lot <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.FIXED_RISK.value,
            constraints_applied=["invalid_tick_metadata"],
            risk_contribution=Decimal("0.0"),
        )

    raw_size = risk_amount / risk_per_lot

    # 5. Reductions
    raw_size = _apply_reductions_v2(
        raw_size,
        drawdown_step_down_multiplier,
        currency_exposure_reduction,
        correlation_cluster_reduction,
        constraints,
    )

    # 6. Normalize and build output
    stop_pips = Decimal("0.0")
    if request.stop_loss_pips is not None:
        stop_pips = Decimal(str(request.stop_loss_pips))
    else:
        pip_size = (
            Decimal("0.01") if symbol_metadata.digits in {2, 3} else Decimal("0.0001")
        )
        stop_pips = stop_price / pip_size

    return _build_final_sizing_result(
        raw_size,
        stop_price,
        stop_pips,
        symbol_metadata,
        SizingMethod.FIXED_RISK.value,
        constraints,
    )


def calculate_fixed_fractional_size(
    request: PositionSizingRequest,
    portfolio_equity: Decimal,
    symbol_metadata: SymbolRiskMetadata,
    config: RiskConfig,
    drawdown_step_down_multiplier: Decimal = Decimal("1.0"),
    currency_exposure_reduction: Decimal = Decimal("1.0"),
    correlation_cluster_reduction: Decimal = Decimal("1.0"),
    market_context: dict[str, Any] | None = None,
) -> PositionSizingResult:
    """Pure calculator sizing position from fixed fractional equity.

    Args:
        request: Sizing request settings.
        portfolio_equity: Portfolio equity balance.
        symbol_metadata: Symbol spec bounds.
        config: Active risk configuration.
        drawdown_step_down_multiplier: Mitigation drawdown factor.
        currency_exposure_reduction: Currency exposure reduction.
        correlation_cluster_reduction: Correlation cluster reduction.
        market_context: Optional context parameters.

    Returns:
        PositionSizingResult: Sizing outcome.
    """
    logger.info("Stateless calculate_fixed_fractional_size called.")
    ctx = market_context or {}
    constraints: list[str] = []

    # 1. Spec validation
    err_res = _pre_validate_inputs(
        symbol_metadata, portfolio_equity, SizingMethod.FIXED_FRACTIONAL.value
    )
    if err_res is not None:
        return err_res

    # 2. Stop distance calculation
    try:
        stop_price = calculate_stop_distance(request, symbol_metadata, ctx)
    except ValueError:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.FIXED_FRACTIONAL.value,
            constraints_applied=["missing_volatility_inputs"],
            risk_contribution=Decimal("0.0"),
        )

    if stop_price <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.FIXED_FRACTIONAL.value,
            constraints_applied=["invalid_stop_distance"],
            risk_contribution=Decimal("0.0"),
        )

    # 3. Risk amount calculation
    risk_pct = request.risk_percent or Decimal("0.02")
    max_risk_pct = getattr(config, "max_risk_per_trade", Decimal("0.02"))

    if risk_pct > max_risk_pct:
        risk_pct = max_risk_pct
        constraints.append("max_risk_per_trade_cap")

    risk_amount = portfolio_equity * Decimal(str(risk_pct))

    # 4. Convert stop distance to risk per lot
    risk_per_lot = convert_stop_distance_to_account_risk(
        stop_price, symbol_metadata, "USD"
    )
    if risk_per_lot <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.FIXED_FRACTIONAL.value,
            constraints_applied=["invalid_tick_metadata"],
            risk_contribution=Decimal("0.0"),
        )

    raw_size = risk_amount / risk_per_lot

    # 5. Reductions
    raw_size = _apply_reductions_v2(
        raw_size,
        drawdown_step_down_multiplier,
        currency_exposure_reduction,
        correlation_cluster_reduction,
        constraints,
    )

    # 6. Normalize and build output
    stop_pips = Decimal("0.0")
    if request.stop_loss_pips is not None:
        stop_pips = Decimal(str(request.stop_loss_pips))
    else:
        pip_size = (
            Decimal("0.01") if symbol_metadata.digits in {2, 3} else Decimal("0.0001")
        )
        stop_pips = stop_price / pip_size

    return _build_final_sizing_result(
        raw_size,
        stop_price,
        stop_pips,
        symbol_metadata,
        SizingMethod.FIXED_FRACTIONAL.value,
        constraints,
    )


def calculate_volatility_adjusted_size(
    request: PositionSizingRequest,
    portfolio_equity: Decimal,
    symbol_metadata: SymbolRiskMetadata,
    config: RiskConfig,
    drawdown_step_down_multiplier: Decimal = Decimal("1.0"),
    currency_exposure_reduction: Decimal = Decimal("1.0"),
    correlation_cluster_reduction: Decimal = Decimal("1.0"),
    market_context: dict[str, Any] | None = None,
) -> PositionSizingResult:
    """Pure calculator sizing position from volatility stops.

    Args:
        request: Sizing request settings.
        portfolio_equity: Portfolio equity balance.
        symbol_metadata: Symbol spec bounds.
        config: Active risk configuration.
        drawdown_step_down_multiplier: Mitigation drawdown factor.
        currency_exposure_reduction: Currency exposure reduction.
        correlation_cluster_reduction: Correlation cluster reduction.
        market_context: Optional context parameters.

    Returns:
        PositionSizingResult: Sizing outcome.
    """
    logger.info("Stateless calculate_volatility_adjusted_size called.")
    ctx = market_context or {}
    constraints: list[str] = []

    # 1. Spec validation
    err_res = _pre_validate_inputs(
        symbol_metadata, portfolio_equity, SizingMethod.VOLATILITY_ADJUSTED.value
    )
    if err_res is not None:
        return err_res

    # 2. Stop distance calculation
    try:
        # Request method override to ensure volatility stops math runs
        req_copy = request.model_copy(
            update={"method": SizingMethod.VOLATILITY_ADJUSTED.value}
        )
        stop_price = calculate_stop_distance(req_copy, symbol_metadata, ctx)
        if ctx.get("m1_volatility") is not None or request.atr_value is not None:
            if ctx.get("m1_volatility") is not None:
                constraints.append("m1_volatility_stop")
            else:
                constraints.append("atr_volatility_stop")
    except ValueError:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.VOLATILITY_ADJUSTED.value,
            constraints_applied=["missing_volatility_inputs"],
            risk_contribution=Decimal("0.0"),
        )

    if stop_price <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.VOLATILITY_ADJUSTED.value,
            constraints_applied=["invalid_stop_distance"],
            risk_contribution=Decimal("0.0"),
        )

    # 3. Risk amount calculation
    risk_pct = request.risk_percent or Decimal("0.02")
    max_risk_pct = getattr(config, "max_risk_per_trade", Decimal("0.02"))

    if risk_pct > max_risk_pct:
        risk_pct = max_risk_pct
        constraints.append("max_risk_per_trade_cap")

    risk_amount = portfolio_equity * Decimal(str(risk_pct))

    # 4. Convert stop distance to risk per lot
    risk_per_lot = convert_stop_distance_to_account_risk(
        stop_price, symbol_metadata, "USD"
    )
    if risk_per_lot <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.VOLATILITY_ADJUSTED.value,
            constraints_applied=["invalid_tick_metadata"],
            risk_contribution=Decimal("0.0"),
        )

    raw_size = risk_amount / risk_per_lot

    # 5. Reductions
    raw_size = _apply_reductions_v2(
        raw_size,
        drawdown_step_down_multiplier,
        currency_exposure_reduction,
        correlation_cluster_reduction,
        constraints,
    )

    # 6. Normalize and build output
    pip_size = (
        Decimal("0.01") if symbol_metadata.digits in {2, 3} else Decimal("0.0001")
    )
    stop_pips = stop_price / pip_size

    return _build_final_sizing_result(
        raw_size,
        stop_price,
        stop_pips,
        symbol_metadata,
        SizingMethod.VOLATILITY_ADJUSTED.value,
        constraints,
    )


def calculate_correlation_adjusted_size(
    request: PositionSizingRequest,
    portfolio_equity: Decimal,
    symbol_metadata: SymbolRiskMetadata,
    config: RiskConfig,
    correlation: CorrelationImpact,
    drawdown_step_down_multiplier: Decimal = Decimal("1.0"),
    currency_exposure_reduction: Decimal = Decimal("1.0"),
    correlation_cluster_reduction: Decimal = Decimal("1.0"),
    market_context: dict[str, Any] | None = None,
) -> PositionSizingResult:
    """Pure calculator sizing position with correlation scaling.

    Args:
        request: Sizing request settings.
        portfolio_equity: Portfolio equity balance.
        symbol_metadata: Symbol spec bounds.
        config: Active risk configuration.
        correlation: CorrelationImpact wrapper containing coefficient.
        drawdown_step_down_multiplier: Mitigation drawdown factor.
        currency_exposure_reduction: Currency exposure reduction.
        correlation_cluster_reduction: Correlation cluster reduction.
        market_context: Optional context parameters.

    Returns:
        PositionSizingResult: Sizing outcome.
    """
    logger.info("Stateless calculate_correlation_adjusted_size called.")
    ctx = market_context or {}
    constraints: list[str] = []

    # 1. Spec validation
    err_res = _pre_validate_inputs(
        symbol_metadata, portfolio_equity, SizingMethod.CORRELATION_ADJUSTED.value
    )
    if err_res is not None:
        return err_res

    # 2. Stop distance calculation
    try:
        stop_price = calculate_stop_distance(request, symbol_metadata, ctx)
    except ValueError:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.CORRELATION_ADJUSTED.value,
            constraints_applied=["missing_volatility_inputs"],
            risk_contribution=Decimal("0.0"),
        )

    if stop_price <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.CORRELATION_ADJUSTED.value,
            constraints_applied=["invalid_stop_distance"],
            risk_contribution=Decimal("0.0"),
        )

    # 3. Risk amount calculation
    risk_pct = request.risk_percent or Decimal("0.02")
    max_risk_pct = getattr(config, "max_risk_per_trade", Decimal("0.02"))

    if risk_pct > max_risk_pct:
        risk_pct = max_risk_pct
        constraints.append("max_risk_per_trade_cap")

    risk_amount = portfolio_equity * Decimal(str(risk_pct))

    # 4. Convert stop distance to risk per lot
    risk_per_lot = convert_stop_distance_to_account_risk(
        stop_price, symbol_metadata, "USD"
    )
    if risk_per_lot <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.CORRELATION_ADJUSTED.value,
            constraints_applied=["invalid_tick_metadata"],
            risk_contribution=Decimal("0.0"),
        )

    raw_size = risk_amount / risk_per_lot

    # 5. Correlation adjustments
    coef = correlation.portfolio_correlation
    mult = max(Decimal("0.1"), Decimal("1.0") - coef * Decimal("0.5"))
    raw_size *= mult
    constraints.append("correlation_adjustment")

    # 6. Reductions
    raw_size = _apply_reductions_v2(
        raw_size,
        drawdown_step_down_multiplier,
        currency_exposure_reduction,
        correlation_cluster_reduction,
        constraints,
    )

    # 7. Normalize and build output
    stop_pips = Decimal("0.0")
    if request.stop_loss_pips is not None:
        stop_pips = Decimal(str(request.stop_loss_pips))
    else:
        pip_size = (
            Decimal("0.01") if symbol_metadata.digits in {2, 3} else Decimal("0.0001")
        )
        stop_pips = stop_price / pip_size

    return _build_final_sizing_result(
        raw_size,
        stop_price,
        stop_pips,
        symbol_metadata,
        SizingMethod.CORRELATION_ADJUSTED.value,
        constraints,
    )


def calculate_milestone_size(
    request: PositionSizingRequest,
    portfolio_equity: Decimal,
    symbol_metadata: SymbolRiskMetadata,
    config: RiskConfig,
    milestones: Sequence[RiskMilestone],
    drawdown_step_down_multiplier: Decimal = Decimal("1.0"),
    currency_exposure_reduction: Decimal = Decimal("1.0"),
    correlation_cluster_reduction: Decimal = Decimal("1.0"),
    market_context: dict[str, Any] | None = None,
) -> PositionSizingResult:
    """Pure calculator sizing position with milestone scaling.

    Args:
        request: Sizing request settings.
        portfolio_equity: Portfolio equity balance.
        symbol_metadata: Symbol spec bounds.
        config: Active risk configuration.
        milestones: Active milestone list configurations.
        drawdown_step_down_multiplier: Mitigation drawdown factor.
        currency_exposure_reduction: Currency exposure reduction.
        correlation_cluster_reduction: Correlation cluster reduction.
        market_context: Optional context parameters.

    Returns:
        PositionSizingResult: Sizing outcome.
    """
    logger.info("Stateless calculate_milestone_size called.")
    ctx = market_context or {}
    constraints: list[str] = []

    # 1. Spec validation
    err_res = _pre_validate_inputs(
        symbol_metadata, portfolio_equity, SizingMethod.MILESTONE.value
    )
    if err_res is not None:
        return err_res

    # 2. Stop distance calculation
    try:
        stop_price = calculate_stop_distance(request, symbol_metadata, ctx)
    except ValueError:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.MILESTONE.value,
            constraints_applied=["missing_volatility_inputs"],
            risk_contribution=Decimal("0.0"),
        )

    if stop_price <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.MILESTONE.value,
            constraints_applied=["invalid_stop_distance"],
            risk_contribution=Decimal("0.0"),
        )

    # 3. Risk amount calculation
    risk_pct = request.risk_percent or Decimal("0.02")
    max_risk_pct = getattr(config, "max_risk_per_trade", Decimal("0.02"))

    if risk_pct > max_risk_pct:
        risk_pct = max_risk_pct
        constraints.append("max_risk_per_trade_cap")

    risk_amount = portfolio_equity * Decimal(str(risk_pct))

    # 4. Convert stop distance to risk per lot
    risk_per_lot = convert_stop_distance_to_account_risk(
        stop_price, symbol_metadata, "USD"
    )
    if risk_per_lot <= 0:
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=SizingMethod.MILESTONE.value,
            constraints_applied=["invalid_tick_metadata"],
            risk_contribution=Decimal("0.0"),
        )

    raw_size = risk_amount / risk_per_lot

    # 5. Milestone adjustments
    for milestone in milestones:
        if milestone.multiplier != 1:
            raw_size *= milestone.multiplier
            constraints.append("milestone_adjustment")

    # 6. Reductions
    raw_size = _apply_reductions_v2(
        raw_size,
        drawdown_step_down_multiplier,
        currency_exposure_reduction,
        correlation_cluster_reduction,
        constraints,
    )

    # 7. Normalize and build output
    stop_pips = Decimal("0.0")
    if request.stop_loss_pips is not None:
        stop_pips = Decimal(str(request.stop_loss_pips))
    else:
        pip_size = (
            Decimal("0.01") if symbol_metadata.digits in {2, 3} else Decimal("0.0001")
        )
        stop_pips = stop_price / pip_size

    return _build_final_sizing_result(
        raw_size,
        stop_price,
        stop_pips,
        symbol_metadata,
        SizingMethod.MILESTONE.value,
        constraints,
    )


def calculate_kelly_reference_size(
    request: PositionSizingRequest,
    portfolio_equity: Decimal,
    symbol_metadata: SymbolRiskMetadata,
    config: RiskConfig,
    evidence: KellyEvidence,
    market_context: dict[str, Any] | None = None,
) -> AdvisorySizingResult:
    """Pure calculator sizing position from statistical Kelly fractions.

    Args:
        request: Sizing request settings.
        portfolio_equity: Portfolio equity balance.
        symbol_metadata: Symbol spec bounds.
        config: Active risk configuration.
        evidence: KellyEvidence performance statistics.
        market_context: Optional context parameters.

    Returns:
        AdvisorySizingResult: advisory outcome.
    """
    logger.info("Stateless calculate_kelly_reference_size called.")
    ctx = market_context or {}
    constraints: list[str] = []

    # 1. Calculate Kelly fraction
    win_rate = evidence.win_rate
    win_loss_ratio = evidence.win_loss_ratio
    trade_count = evidence.historical_trade_count

    min_trades = evidence.min_kelly_trades or config.min_kelly_trades

    if win_loss_ratio > 0:
        kelly_fraction = win_rate - (Decimal("1.0") - win_rate) / win_loss_ratio
    else:
        kelly_fraction = Decimal("0.0")

    kelly_fraction = max(Decimal("0.0"), kelly_fraction)
    kelly_fraction *= evidence.kelly_multiplier

    if trade_count < min_trades:
        constraints.append("kelly_advisory_insufficient_evidence")
        return AdvisorySizingResult(
            calculated_volume=Decimal("0.0"),
            kelly_fraction_applied=Decimal("0.0"),
            constraints_applied=constraints,
            is_advisory_only=True,
        )

    constraints.append("kelly_fraction_applied")

    # Resolve whether fractional Kelly is globally enabled
    enable_fractional = (
        evidence.enable_fractional_kelly
        or ctx.get("enable_fractional_kelly", False)
        or config.experimental_features.get("enable_fractional_kelly", False)
    )

    is_advisory_only = not enable_fractional
    if is_advisory_only:
        constraints.append("kelly_advisory_only")

    try:
        stop_price = calculate_stop_distance(request, symbol_metadata, ctx)
    except ValueError:
        stop_price = Decimal("0.0")

    if stop_price > 0:
        risk_per_lot = convert_stop_distance_to_account_risk(
            stop_price, symbol_metadata, "USD"
        )
        volume = (kelly_fraction * portfolio_equity) / risk_per_lot
    else:
        volume = (kelly_fraction * portfolio_equity) / (
            symbol_metadata.contract_size * symbol_metadata.conversion_rate
        )

    return AdvisorySizingResult(
        calculated_volume=volume,
        kelly_fraction_applied=kelly_fraction,
        constraints_applied=constraints,
        is_advisory_only=is_advisory_only,
    )


def calculate_position_size(  # noqa: C901, PLR0911
    request: PositionSizingRequest,
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> PositionSizingResult:
    """Position sizing gateway routing requests to pure stateless calculators.

    Args:
        request: Target sizing parameters request.
        portfolio_state: Active portfolio account state.
        market_context: Live volatility and step specification parameters.
        config: Sizing limits configuration profile.

    Returns:
        PositionSizingResult: Validated target position order lot.
    """
    logger.info("calculate_position_size wrapper called for %s", request.symbol)
    method_str = request.method or SizingMethod.VOLATILITY_ADJUSTED.value
    try:
        method = SizingMethod(method_str)
    except ValueError:
        method = SizingMethod.VOLATILITY_ADJUSTED

    req_keys = ["volume_min", "volume_max", "volume_step", "contract_size"]
    if any(market_context.get(k) is None for k in req_keys):
        return PositionSizingResult(
            calculated_volume=Decimal("0.0"),
            sizing_method=method_str,
            constraints_applied=["missing_symbol_metadata"],
            risk_contribution=Decimal("0.0"),
        )

    # 1. Map market_context parameters to SymbolRiskMetadata
    symbol_metadata = SymbolRiskMetadata(
        symbol=request.symbol,
        volume_min=Decimal(str(market_context.get("volume_min", "0.01"))),
        volume_max=Decimal(str(market_context.get("volume_max", "100.00"))),
        volume_step=Decimal(str(market_context.get("volume_step", "0.01"))),
        contract_size=Decimal(str(market_context.get("contract_size", "100000.0"))),
        digits=int(market_context.get("digits", 5)),
        tick_size=Decimal(str(market_context.get("tick_size")))
        if market_context.get("tick_size") is not None
        else None,
        tick_value=Decimal(str(market_context.get("tick_value")))
        if market_context.get("tick_value") is not None
        else None,
        conversion_rate=Decimal(str(market_context.get("conversion_rate", "1.0"))),
    )

    # Extract reductions from market_context
    drawdown_step_down = Decimal(
        str(market_context.get("drawdown_step_down_multiplier", "1.0"))
    )
    currency_exposure = Decimal(
        str(market_context.get("currency_exposure_reduction", "1.0"))
    )
    correlation_cluster = Decimal(
        str(market_context.get("correlation_cluster_reduction", "1.0"))
    )

    if method == SizingMethod.FIXED_LOT:
        constraints: list[str] = []
        raw_size = Decimal(str(request.fixed_volume or Decimal("0.10")))
        raw_size = _apply_reductions_v2(
            raw_size,
            drawdown_step_down,
            currency_exposure,
            correlation_cluster,
            constraints,
        )
        return _build_final_sizing_result(
            raw_size,
            stop_distance_price=Decimal("0.0"),
            stop_pips=Decimal("0.0"),
            symbol_metadata=symbol_metadata,
            sizing_method=method.value,
            constraints=constraints,
        )

    if method == SizingMethod.FIXED_RISK:
        return calculate_fixed_risk_size(
            request=request,
            portfolio_equity=portfolio_state.equity,
            symbol_metadata=symbol_metadata,
            config=config,
            drawdown_step_down_multiplier=drawdown_step_down,
            currency_exposure_reduction=currency_exposure,
            correlation_cluster_reduction=correlation_cluster,
            market_context=market_context,
        )

    if method == SizingMethod.FIXED_FRACTIONAL:
        return calculate_fixed_fractional_size(
            request=request,
            portfolio_equity=portfolio_state.equity,
            symbol_metadata=symbol_metadata,
            config=config,
            drawdown_step_down_multiplier=drawdown_step_down,
            currency_exposure_reduction=currency_exposure,
            correlation_cluster_reduction=correlation_cluster,
            market_context=market_context,
        )

    if method == SizingMethod.VOLATILITY_ADJUSTED:
        return calculate_volatility_adjusted_size(
            request=request,
            portfolio_equity=portfolio_state.equity,
            symbol_metadata=symbol_metadata,
            config=config,
            drawdown_step_down_multiplier=drawdown_step_down,
            currency_exposure_reduction=currency_exposure,
            correlation_cluster_reduction=correlation_cluster,
            market_context=market_context,
        )

    if method == SizingMethod.CORRELATION_ADJUSTED:
        coef = Decimal(str(market_context.get("portfolio_correlation", "0.0")))
        correlation_impact = CorrelationImpact(portfolio_correlation=coef)
        return calculate_correlation_adjusted_size(
            request=request,
            portfolio_equity=portfolio_state.equity,
            symbol_metadata=symbol_metadata,
            config=config,
            correlation=correlation_impact,
            drawdown_step_down_multiplier=drawdown_step_down,
            currency_exposure_reduction=currency_exposure,
            correlation_cluster_reduction=correlation_cluster,
            market_context=market_context,
        )

    if method == SizingMethod.MILESTONE:
        mult = Decimal(str(market_context.get("milestone_multiplier", "1.0")))
        milestones = [RiskMilestone(name="multiplier_adjust", multiplier=mult)]
        return calculate_milestone_size(
            request=request,
            portfolio_equity=portfolio_state.equity,
            symbol_metadata=symbol_metadata,
            config=config,
            milestones=milestones,
            drawdown_step_down_multiplier=drawdown_step_down,
            currency_exposure_reduction=currency_exposure,
            correlation_cluster_reduction=correlation_cluster,
            market_context=market_context,
        )

    if method == SizingMethod.KELLY:
        evidence = KellyEvidence(
            win_rate=Decimal(str(market_context.get("kelly_win_rate", "0.50"))),
            win_loss_ratio=Decimal(
                str(market_context.get("kelly_win_loss_ratio", "1.5"))
            ),
            historical_trade_count=int(market_context.get("historical_trade_count", 0)),
            min_kelly_trades=int(
                market_context.get("kelly_min_trades", config.min_kelly_trades)
            ),
            kelly_multiplier=Decimal(
                str(market_context.get("kelly_multiplier", "1.0"))
            ),
            enable_fractional_kelly=bool(
                market_context.get("enable_fractional_kelly", False)
            ),
        )
        res_kelly = calculate_kelly_reference_size(
            request=request,
            portfolio_equity=portfolio_state.equity,
            symbol_metadata=symbol_metadata,
            config=config,
            evidence=evidence,
            market_context=market_context,
        )
        is_live = market_context.get("is_live", False)
        allow_live = config.allow_live_execution

        # If it is advisory only AND we are in live/exec mode, return 0.0 volume
        if res_kelly.is_advisory_only and (is_live or allow_live):
            return PositionSizingResult(
                calculated_volume=Decimal("0.0"),
                sizing_method=method.value,
                constraints_applied=res_kelly.constraints_applied,
                risk_contribution=Decimal("0.0"),
            )

        try:
            stop_price = calculate_stop_distance(
                request, symbol_metadata, market_context
            )
        except ValueError:
            stop_price = Decimal("0.0")

        return _build_final_sizing_result(
            res_kelly.calculated_volume,
            stop_price,
            request.stop_loss_pips or Decimal("0.0"),
            symbol_metadata,
            method.value,
            res_kelly.constraints_applied,
        )

    return PositionSizingResult(
        calculated_volume=Decimal("0.0"),
        sizing_method=method.value,
        constraints_applied=["unknown_sizing_method"],
        risk_contribution=Decimal("0.0"),
    )


class VolatilitySizingEngine:
    """Position sizing engine coordinating dynamic calculations."""

    def __init__(self, config: RiskConfig) -> None:
        """Initialize engine with active configuration."""
        self.config = config

    def calculate_position_size(
        self,
        request: PositionSizingRequest,
        portfolio_state: PortfolioState,
        market_context: dict[str, Any],
    ) -> PositionSizingResult:
        """Calculate position sizing using active configuration."""
        return calculate_position_size(
            request, portfolio_state, market_context, self.config
        )
