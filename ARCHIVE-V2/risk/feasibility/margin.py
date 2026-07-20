"""Margin governance engine.

Evaluates current and projected margin, free margin, leverage, and
exit-liquidity stress for a proposed trade against account and portfolio
constraints. Also exposes a pure, canonically-typed V2 calculation surface
(:func:`calculate_current_margin_usage`, :func:`calculate_projected_margin_usage`,
:func:`calculate_free_margin_after_reservations`, :func:`check_margin_limits`)
alongside the original V1 ``PortfolioState``/``market_context`` calculation surface.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.exposure import (
    _resolve_base_quote as _orig_resolve_base_quote,
)
from app.services.risk.exposure import (
    _resolve_conversion_rate,
)
from app.services.risk.limits import LimitResult
from app.services.risk.models import (
    AccountRiskSnapshot,
    MarginRiskSnapshot,
    PendingOrderRiskSnapshot,
    PortfolioRiskSnapshot,
    PortfolioState,
    ProposedTrade,
    RiskConfig,
    RiskContract,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)
from app.utils.logger import logger
from pydantic import Field

if TYPE_CHECKING:
    from app.services.risk.policy.contracts import EffectiveRiskPolicy


class MarginRequirement(RiskContract):
    """Calculated margin requirements and utility metrics."""

    current_margin: Decimal = Field(..., description="Current utilized margin.")
    projected_margin: Decimal = Field(
        ..., description="Projected margin after candidate trade."
    )
    margin_usage: Decimal = Field(..., description="Projected margin usage ratio.")
    pass_status: bool = Field(
        ..., description="True if within max margin utilization limit."
    )


class LeverageSnapshot(RiskContract):
    """Effective leverage metrics compared against caps."""

    effective_leverage: Decimal = Field(
        ..., description="Current/projected effective leverage."
    )
    leverage_cap: Decimal = Field(
        ..., description="Configured maximum effective leverage."
    )
    pass_status: bool = Field(..., description="True if within leverage limits.")


class LiquiditySnapshot(RiskContract):
    """Exit liquidity shock metrics and remaining free margin."""

    exit_liquidity_loss: Decimal = Field(
        ..., description="Simulated exit cost transaction loss."
    )
    remaining_free_margin: Decimal = Field(
        ..., description="Projected free margin after orders/trade."
    )
    pass_status: bool = Field(
        ..., description="True if simulated exit loss is less than free margin."
    )


def _resolve_base_quote(
    symbol: str, market_context: dict[str, Any] | None = None
) -> tuple[str, str]:
    """Resolve base and quote currencies, wrapper for optional market_context.

    Args:
        symbol: Instrument symbol (e.g. "EURUSD").
        market_context: Optional market context dictionary carrying overrides.

    Returns:
        tuple[str, str]: Base and quote currency codes.
    """
    ctx = market_context if market_context is not None else {}
    return _orig_resolve_base_quote(symbol, ctx)


def calculate_current_margin(portfolio_state: PortfolioState) -> Decimal:
    """Calculate the total margin currently utilized by open positions.

    Args:
        portfolio_state: Current portfolio snapshot.

    Returns:
        Decimal total margin required in account currency.
    """
    total = sum(
        (pos.margin_required for pos in portfolio_state.positions), Decimal("0.0")
    )
    logger.debug(f"Calculated current margin usage: {total}.")
    return total


def _resolve_proposed_price(
    symbol: str,
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
) -> Decimal:
    """Helper to resolve proposed trade price from positions or market context."""
    for pos in portfolio_state.positions:
        if pos.symbol == symbol:
            return pos.current_price

    price_raw = market_context.get(f"{symbol}_price")
    if price_raw is not None:
        return Decimal(str(price_raw))

    bars = market_context.get("market_data", {}).get(symbol, [])
    if bars:
        last_bar = bars[-1]
        price_str = (
            last_bar.get("close", "0.0")
            if isinstance(last_bar, dict)
            else getattr(last_bar, "close", "0.0")
        )
        return Decimal(str(price_str))

    return Decimal("0.0")


def calculate_projected_margin(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> Decimal:
    """Calculate projected margin requirement after executing candidate trade.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Optional proposed candidate trade.
        market_context: Dictionary containing rates, leverage, and contract sizes.
        config: Active risk configuration.

    Returns:
        Decimal total projected margin.

    Raises:
        ValidationError: If required broker margin metadata is missing.
    """
    current_margin = calculate_current_margin(portfolio_state)
    if proposed_trade is None:
        logger.info("No proposed trade; projected margin equals current margin.")
        return current_margin

    symbol = proposed_trade.symbol
    price = proposed_trade.price

    if price == Decimal("0.0"):
        price = _resolve_proposed_price(symbol, portfolio_state, market_context)

    if price <= Decimal("0.0"):
        msg = f"Missing price metadata for {symbol}."
        logger.error(msg)
        raise ValidationError(msg)

    c_size_raw = market_context.get(f"{symbol}_contract_size") or market_context.get(
        "contract_size"
    )
    if c_size_raw is None:
        msg = f"Missing contract size metadata for {symbol}."
        logger.error(msg)
        raise ValidationError(msg)
    contract_size = Decimal(str(c_size_raw))

    leverage_raw = (
        market_context.get(f"{symbol}_leverage")
        or market_context.get("leverage")
        or config.max_effective_leverage
    )
    if leverage_raw is None:
        msg = f"Missing leverage metadata for {symbol}."
        logger.error(msg)
        raise ValidationError(msg)
    leverage = Decimal(str(leverage_raw))

    # Enforce leverage caps stricter than broker maximum
    leverage = min(leverage, config.max_effective_leverage)

    margin_quote = (proposed_trade.volume * contract_size * price) / leverage

    _, quote_ccy = _resolve_base_quote(symbol)
    rate = _resolve_conversion_rate(
        quote_ccy, portfolio_state.currency.upper(), market_context
    )
    proposed_margin_acct = margin_quote * rate
    logger.debug(
        f"Proposed trade margin in account currency for {symbol}: "
        f"{proposed_margin_acct}."
    )

    total = current_margin + proposed_margin_acct
    logger.info(f"Calculated projected margin for {symbol}: {total}.")
    return total


def calculate_free_margin_after_orders(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> Decimal:
    """Calculate remaining free margin.

    Accounts for open positions, proposed trade, and pending orders.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Optional proposed candidate trade.
        market_context: Dictionary containing rates, leverage, and contract sizes.
        config: Active risk configuration.

    Returns:
        Decimal remaining free margin.
    """
    equity = portfolio_state.equity
    projected_margin = calculate_projected_margin(
        portfolio_state, proposed_trade, market_context, config
    )

    pending_margin = Decimal("0.0")
    policy = config.pending_order_policy.lower()

    if policy != "ignore":
        for order in portfolio_state.orders:
            status = (
                order.get("status")
                if isinstance(order, dict)
                else getattr(order, "status", None)
            )
            if status != "active":
                continue

            symbol = (
                order.get("symbol")
                if isinstance(order, dict)
                else getattr(order, "symbol", None)
            )
            if not isinstance(symbol, str):
                continue
            volume = Decimal(
                str(
                    order.get("quantity") if isinstance(order, dict) else order.quantity
                )
            )
            price = Decimal(
                str(
                    order.get("price")
                    if isinstance(order, dict)
                    else getattr(order, "price", Decimal("0.0"))
                )
            )

            c_size_raw = market_context.get(
                f"{symbol}_contract_size"
            ) or market_context.get("contract_size")
            if c_size_raw is None:
                continue
            contract_size = Decimal(str(c_size_raw))

            leverage_raw = (
                market_context.get(f"{symbol}_leverage")
                or market_context.get("leverage")
                or config.max_effective_leverage
            )
            if leverage_raw is None:
                continue
            leverage = Decimal(str(leverage_raw))
            leverage = min(leverage, config.max_effective_leverage)

            margin_quote = (volume * contract_size * price) / leverage
            _, quote_ccy = _resolve_base_quote(symbol)
            rate = _resolve_conversion_rate(
                quote_ccy, portfolio_state.currency.upper(), market_context
            )
            order_margin = margin_quote * rate

            if policy == "probability-weighted":
                prob = Decimal(
                    str(
                        order.get("probability", 1.0)
                        if isinstance(order, dict)
                        else getattr(order, "probability", 1.0)
                    )
                )
                pending_margin += order_margin * prob
            elif policy == "near-market-only":
                distance_pips = Decimal(
                    str(
                        order.get("distance_pips", 999.0)
                        if isinstance(order, dict)
                        else getattr(order, "distance_pips", 999.0)
                    )
                )
                if distance_pips <= Decimal("50.0"):
                    pending_margin += order_margin
            else:  # full-potential / probability-weighted
                pending_margin += order_margin

    free_margin = max(Decimal("0.0"), equity - projected_margin - pending_margin)
    logger.info(
        f"Calculated free margin after orders under '{policy}' policy: {free_margin}."
    )
    return free_margin


def evaluate_margin_governance(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> MarginRiskSnapshot:
    """Evaluate account-level margin metrics and build a snapshot.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposed_trade: Candidate proposed trade.
        market_context: Market details.
        config: Active risk configuration.

    Returns:
        MarginRiskSnapshot with evaluation metrics.
    """
    projected_margin = calculate_projected_margin(
        portfolio_state, proposed_trade, market_context, config
    )
    free_margin = calculate_free_margin_after_orders(
        portfolio_state, proposed_trade, market_context, config
    )

    equity = portfolio_state.equity
    margin_usage = (
        projected_margin / equity if equity > Decimal("0.0") else Decimal("1.0")
    )

    total_gross = Decimal("0.0")
    for pos in portfolio_state.positions:
        symbol = pos.symbol
        c_size_raw = market_context.get(
            f"{symbol}_contract_size"
        ) or market_context.get("contract_size", "100000.0")
        contract_size = Decimal(str(c_size_raw))
        exposure_quote = pos.quantity * contract_size * pos.current_price
        _, quote_ccy = _resolve_base_quote(symbol)
        rate = _resolve_conversion_rate(
            quote_ccy, portfolio_state.currency.upper(), market_context
        )
        total_gross += exposure_quote * rate

    if proposed_trade is not None:
        symbol = proposed_trade.symbol
        price = proposed_trade.price
        if price == Decimal("0.0"):
            for pos in portfolio_state.positions:
                if pos.symbol == symbol:
                    price = pos.current_price
                    break
        if price == Decimal("0.0"):
            price_raw = market_context.get(f"{symbol}_price")
            if price_raw is not None:
                price = Decimal(str(price_raw))

        c_size_raw = market_context.get(
            f"{symbol}_contract_size"
        ) or market_context.get("contract_size", "100000.0")
        contract_size = Decimal(str(c_size_raw))
        exposure_quote = proposed_trade.volume * contract_size * price
        _, quote_ccy = _resolve_base_quote(symbol)
        rate = _resolve_conversion_rate(
            quote_ccy, portfolio_state.currency.upper(), market_context
        )
        total_gross += exposure_quote * rate

    effective_leverage = (
        total_gross / equity if equity > Decimal("0.0") else Decimal("500.0")
    )
    logger.info(
        f"Evaluated margin governance: margin_usage={margin_usage}, "
        f"leverage={effective_leverage}."
    )

    return MarginRiskSnapshot(
        projected_margin=projected_margin,
        free_margin=free_margin,
        margin_usage=margin_usage,
        leverage=effective_leverage,
    )


def exit_liquidity_stress_check(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
    spread_multiplier: Decimal = Decimal("5.0"),
) -> tuple[bool, Decimal]:
    """Check if exit transaction costs under spread widening spikes triggers insolvency.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposed_trade: Candidate proposed trade.
        market_context: Market details.
        config: Active risk configuration.
        spread_multiplier: Shock factor multiplier to widen spreads.

    Returns:
        tuple (pass_status: bool, exit_liquidity_loss: Decimal)
    """
    account_ccy = portfolio_state.currency.upper()
    exit_liquidity_loss = Decimal("0.0")

    for pos in portfolio_state.positions:
        symbol = pos.symbol
        spread = Decimal(str(market_context.get(f"{symbol}_spread", "0.0002")))
        c_size_raw = market_context.get(
            f"{symbol}_contract_size"
        ) or market_context.get("contract_size", "100000.0")
        contract_size = Decimal(str(c_size_raw))

        cost_quote = pos.quantity * contract_size * spread * spread_multiplier
        _, quote_ccy = _resolve_base_quote(symbol)
        rate = _resolve_conversion_rate(quote_ccy, account_ccy, market_context)
        exit_liquidity_loss += cost_quote * rate

    if proposed_trade is not None:
        symbol = proposed_trade.symbol
        spread = Decimal(str(market_context.get(f"{symbol}_spread", "0.0002")))
        c_size_raw = market_context.get(
            f"{symbol}_contract_size"
        ) or market_context.get("contract_size", "100000.0")
        contract_size = Decimal(str(c_size_raw))

        cost_quote = proposed_trade.volume * contract_size * spread * spread_multiplier
        _, quote_ccy = _resolve_base_quote(symbol)
        rate = _resolve_conversion_rate(quote_ccy, account_ccy, market_context)
        exit_liquidity_loss += cost_quote * rate

    projected_free = calculate_free_margin_after_orders(
        portfolio_state, proposed_trade, market_context, config
    )
    pass_status = exit_liquidity_loss < projected_free
    logger.info(
        f"Exit liquidity stress check ({spread_multiplier}x spread): "
        f"pass={pass_status}, loss={exit_liquidity_loss}."
    )

    return pass_status, exit_liquidity_loss


def calculate_margin_requirement(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> Decimal:
    """Calculate projected margin requirement after executing candidate trade.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Optional proposed candidate trade.
        market_context: Dictionary containing rates, leverage, and contract sizes.
        config: Active risk configuration.

    Returns:
        Decimal projected margin requirement.
    """
    logger.debug(
        "calculate_margin_requirement delegating to calculate_projected_margin."
    )
    return calculate_projected_margin(
        portfolio_state, proposed_trade, market_context, config
    )


def calculate_free_margin_after_trade(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> Decimal:
    """Calculate remaining free margin after trade and pending orders.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Optional proposed candidate trade.
        market_context: Dictionary containing rates, leverage, and contract sizes.
        config: Active risk configuration.

    Returns:
        Decimal projected remaining free margin.
    """
    logger.debug(
        "calculate_free_margin_after_trade delegating to "
        "calculate_free_margin_after_orders."
    )
    return calculate_free_margin_after_orders(
        portfolio_state, proposed_trade, market_context, config
    )


def check_margin_usage(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Check account-level margin utilization limits.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposed_trade: Candidate proposed trade.
        market_context: Market details.
        config: Active risk configuration.

    Returns:
        LimitResult showing margin approval status.
    """
    try:
        projected_margin = calculate_projected_margin(
            portfolio_state, proposed_trade, market_context, config
        )
    except ValidationError as e:
        logger.error(f"Margin metadata evaluation failed: {e}")
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=f"Margin metadata evaluation failed: {e}",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    equity = portfolio_state.equity
    margin_usage = (
        projected_margin / equity if equity > Decimal("0.0") else Decimal("1.0")
    )

    if margin_usage > config.max_margin_utilization_pct:
        logger.info(f"Margin utilization limit breached: {margin_usage:.2%}.")
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.MARGIN_BREACH,
            message=(
                f"Margin utilization limit breached: {margin_usage:.2%} > "
                f"{config.max_margin_utilization_pct:.2%}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={
                "margin_usage": float(margin_usage),
                "projected_margin": float(projected_margin),
            },
        )

    logger.info(f"Margin utilization is within safe limits: {margin_usage:.2%}.")
    return LimitResult(
        limit_name="margin_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Margin utilization is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
        details={
            "margin_usage": float(margin_usage),
            "projected_margin": float(projected_margin),
        },
    )


def check_leverage_limit(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Check effective leverage limits.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposed_trade: Candidate proposed trade.
        market_context: Market details.
        config: Active risk configuration.

    Returns:
        LimitResult showing leverage approval status.
    """
    total_gross = Decimal("0.0")
    for pos in portfolio_state.positions:
        symbol = pos.symbol
        c_size_raw = market_context.get(
            f"{symbol}_contract_size"
        ) or market_context.get("contract_size", "100000.0")
        contract_size = Decimal(str(c_size_raw))
        exposure_quote = pos.quantity * contract_size * pos.current_price
        _, quote_ccy = _resolve_base_quote(symbol)
        rate = _resolve_conversion_rate(
            quote_ccy, portfolio_state.currency.upper(), market_context
        )
        total_gross += exposure_quote * rate

    if proposed_trade is not None:
        symbol = proposed_trade.symbol
        price = proposed_trade.price
        if price == Decimal("0.0"):
            price = _resolve_proposed_price(symbol, portfolio_state, market_context)

        c_size_raw = market_context.get(
            f"{symbol}_contract_size"
        ) or market_context.get("contract_size", "100000.0")
        contract_size = Decimal(str(c_size_raw))
        exposure_quote = proposed_trade.volume * contract_size * price
        _, quote_ccy = _resolve_base_quote(symbol)
        rate = _resolve_conversion_rate(
            quote_ccy, portfolio_state.currency.upper(), market_context
        )
        total_gross += exposure_quote * rate

    equity = portfolio_state.equity
    effective_leverage = (
        total_gross / equity if equity > Decimal("0.0") else Decimal("500.0")
    )

    if effective_leverage > config.max_effective_leverage:
        logger.info(f"Leverage limit breached: {effective_leverage:.2f}x.")
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.LEVERAGE_BREACH,
            message=(
                f"Effective leverage limit breached: {effective_leverage:.2f} > "
                f"{config.max_effective_leverage:.2f}."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"leverage": float(effective_leverage)},
        )

    logger.info(f"Effective leverage is within safe limits: {effective_leverage:.2f}x.")
    return LimitResult(
        limit_name="margin_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Effective leverage is within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
        details={"leverage": float(effective_leverage)},
    )


def check_exit_liquidity(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
    spread_multiplier: Decimal = Decimal("5.0"),
) -> LimitResult:
    """Check exit liquidity stress impact.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposed_trade: Candidate proposed trade.
        market_context: Market details.
        config: Active risk configuration.
        spread_multiplier: Shock factor multiplier to widen spreads.

    Returns:
        LimitResult showing exit liquidity approval status.
    """
    exit_pass, exit_loss = exit_liquidity_stress_check(
        portfolio_state, proposed_trade, market_context, config, spread_multiplier
    )

    if not exit_pass:
        logger.info(f"Exit-liquidity stress check failed: projected loss {exit_loss}.")
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.MARGIN_BREACH,
            message=(
                f"Exit-liquidity stress check failed: projected loss {exit_loss:.2f} "
                f"exceeds remaining free margin."
            ),
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"exit_loss": float(exit_loss)},
        )

    logger.info("Exit-liquidity stress check passed.")
    return LimitResult(
        limit_name="margin_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Exit-liquidity stress check passed.",
        severity=RiskSeverity.INFO,
        breached=False,
        details={"exit_loss": float(exit_loss)},
    )


def check_strategy_margin_limit(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult | None:
    """Check strategy-level margin allocation ceilings.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposed_trade: Optional proposed candidate trade.
        market_context: Market details.
        config: Active risk configuration.

    Returns:
        LimitResult if limit applies and is breached/blocked, else None.
    """
    if proposed_trade is None:
        logger.debug("No proposed trade; strategy margin limit check skipped.")
        return None

    strategy_margin_cap = portfolio_state.strategy_allocations.get(
        proposed_trade.strategy_id
    )
    if strategy_margin_cap is None:
        logger.debug(
            f"No strategy margin cap configured for '{proposed_trade.strategy_id}'."
        )
        return None

    strategy_margin = Decimal("0.0")
    for pos in portfolio_state.positions:
        if pos.strategy_id == proposed_trade.strategy_id:
            strategy_margin += pos.margin_required

    try:
        snapshot = evaluate_margin_governance(
            portfolio_state, proposed_trade, market_context, config
        )
    except ValidationError as e:
        logger.error(f"Margin metadata evaluation failed: {e}")
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=f"Margin metadata evaluation failed: {e}",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    proposed_margin = snapshot.projected_margin - sum(
        (p.margin_required for p in portfolio_state.positions), Decimal("0.0")
    )
    total_strat_margin = strategy_margin + proposed_margin

    if total_strat_margin > strategy_margin_cap:
        logger.info(
            f"Strategy margin limit breached for '{proposed_trade.strategy_id}': "
            f"{total_strat_margin} > {strategy_margin_cap}."
        )
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.CONCENTRATION_BREACH,
            message=(
                f"Strategy margin limit breached for "
                f"'{proposed_trade.strategy_id}': "
                f"{total_strat_margin:.2f} USD > "
                f"{strategy_margin_cap:.2f} USD limit."
            ),
            severity=RiskSeverity.SOFT_BREACH,
            breached=True,
            details=snapshot.model_dump(),
        )

    return None


def verify_margin_limits(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Enforce margin utilization, leverage caps, and strategy margin limits.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposed_trade: Optional candidate proposed trade.
        market_context: Market details.
        config: Active risk configuration.

    Returns:
        LimitResult showing margin approval status.
    """
    logger.info("Running full margin limits verification sequence.")

    margin_res = check_margin_usage(
        portfolio_state, proposed_trade, market_context, config
    )
    if margin_res.breached:
        return margin_res

    leverage_res = check_leverage_limit(
        portfolio_state, proposed_trade, market_context, config
    )
    if leverage_res.breached:
        return leverage_res

    strat_res = check_strategy_margin_limit(
        portfolio_state, proposed_trade, market_context, config
    )
    if strat_res is not None and strat_res.breached:
        return strat_res

    exit_res = check_exit_liquidity(
        portfolio_state, proposed_trade, market_context, config
    )
    if exit_res.breached:
        return exit_res

    try:
        snapshot = evaluate_margin_governance(
            portfolio_state, proposed_trade, market_context, config
        )
    except ValidationError as e:
        logger.error(f"Margin metadata evaluation failed: {e}")
        return LimitResult(
            limit_name="margin_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.INVALID_INPUT,
            message=f"Margin metadata evaluation failed: {e}",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )

    logger.info("Margin limits verification sequence approved.")
    return LimitResult(
        limit_name="margin_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Margin utilization and leverage are within safe limits.",
        severity=RiskSeverity.INFO,
        breached=False,
        details=snapshot.model_dump(),
    )


class MarginRiskEngine:
    """Engine for evaluating margin requirements, leverage, and exit liquidity."""

    def __init__(self, config: RiskConfig) -> None:
        """Initialize the engine with configuration.

        Args:
            config: Active risk configuration profile.
        """
        self.config = config
        logger.debug("MarginRiskEngine initialized.")

    def evaluate_margin(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
    ) -> MarginRequirement:
        """Calculate margin requirements for current and projected states.

        Args:
            portfolio_state: Current portfolio state.
            proposed_trade: Optional candidate proposed trade.
            market_context: Market details.

        Returns:
            MarginRequirement containing evaluation outcomes.
        """
        current_margin = calculate_current_margin(portfolio_state)
        projected_margin = calculate_margin_requirement(
            portfolio_state, proposed_trade, market_context, self.config
        )
        equity = portfolio_state.equity
        margin_usage = (
            projected_margin / equity if equity > Decimal("0.0") else Decimal("1.0")
        )
        pass_status = margin_usage <= self.config.max_margin_utilization_pct
        logger.info(f"MarginRiskEngine.evaluate_margin pass_status={pass_status}.")

        return MarginRequirement(
            current_margin=current_margin,
            projected_margin=projected_margin,
            margin_usage=margin_usage,
            pass_status=pass_status,
        )

    def evaluate_leverage(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
    ) -> LeverageSnapshot:
        """Evaluate effective leverage against limits.

        Args:
            portfolio_state: Current portfolio state.
            proposed_trade: Optional candidate proposed trade.
            market_context: Market details.

        Returns:
            LeverageSnapshot containing leverage evaluation metrics.
        """
        res = check_leverage_limit(
            portfolio_state, proposed_trade, market_context, self.config
        )

        total_gross = Decimal("0.0")
        for pos in portfolio_state.positions:
            symbol = pos.symbol
            c_size_raw = market_context.get(
                f"{symbol}_contract_size"
            ) or market_context.get("contract_size", "100000.0")
            contract_size = Decimal(str(c_size_raw))
            exposure_quote = pos.quantity * contract_size * pos.current_price
            _, quote_ccy = _resolve_base_quote(symbol)
            rate = _resolve_conversion_rate(
                quote_ccy, portfolio_state.currency.upper(), market_context
            )
            total_gross += exposure_quote * rate

        if proposed_trade is not None:
            symbol = proposed_trade.symbol
            price = proposed_trade.price
            if price == Decimal("0.0"):
                price = _resolve_proposed_price(symbol, portfolio_state, market_context)

            c_size_raw = market_context.get(
                f"{symbol}_contract_size"
            ) or market_context.get("contract_size", "100000.0")
            contract_size = Decimal(str(c_size_raw))
            exposure_quote = proposed_trade.volume * contract_size * price
            _, quote_ccy = _resolve_base_quote(symbol)
            rate = _resolve_conversion_rate(
                quote_ccy, portfolio_state.currency.upper(), market_context
            )
            total_gross += exposure_quote * rate

        equity = portfolio_state.equity
        effective_leverage = (
            total_gross / equity if equity > Decimal("0.0") else Decimal("500.0")
        )
        logger.info(
            f"MarginRiskEngine.evaluate_leverage effective_leverage="
            f"{effective_leverage}."
        )

        return LeverageSnapshot(
            effective_leverage=effective_leverage,
            leverage_cap=self.config.max_effective_leverage,
            pass_status=not res.breached,
        )

    def evaluate_exit_liquidity(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        spread_multiplier: Decimal = Decimal("5.0"),
    ) -> LiquiditySnapshot:
        """Evaluate exit liquidity stress impact.

        Args:
            portfolio_state: Current portfolio state.
            proposed_trade: Optional candidate proposed trade.
            market_context: Market details.
            spread_multiplier: Wide spread multiplier factor.

        Returns:
            LiquiditySnapshot containing liquidity evaluation metrics.
        """
        pass_status, exit_loss = exit_liquidity_stress_check(
            portfolio_state,
            proposed_trade,
            market_context,
            self.config,
            spread_multiplier,
        )
        remaining_free = calculate_free_margin_after_trade(
            portfolio_state, proposed_trade, market_context, self.config
        )
        logger.info(
            f"MarginRiskEngine.evaluate_exit_liquidity pass_status={pass_status}."
        )

        return LiquiditySnapshot(
            exit_liquidity_loss=exit_loss,
            remaining_free_margin=remaining_free,
            pass_status=pass_status,
        )


def calculate_current_margin_usage(
    account: AccountRiskSnapshot, portfolio: PortfolioRiskSnapshot
) -> MarginRiskSnapshot:
    """Derive the current margin usage snapshot from canonical account evidence.

    Args:
        account: Canonical account-level risk snapshot.
        portfolio: Canonical portfolio-level risk snapshot.

    Returns:
        MarginRiskSnapshot: Current margin projection, free margin, usage, and
            leverage metrics.
    """
    logger.info("Calculating current margin usage from canonical snapshots.")
    equity = account.equity
    margin_usage = (
        account.margin_used / equity if equity > Decimal("0.0") else Decimal("1.0")
    )
    leverage = (
        account.leverage
        if account.leverage > 0
        else portfolio.exposure
        / (equity if equity > Decimal("0.0") else Decimal("1.0"))
    )
    logger.debug(f"Current margin usage snapshot: usage={margin_usage}.")
    return MarginRiskSnapshot(
        projected_margin=account.margin_used,
        free_margin=account.free_margin,
        margin_usage=margin_usage,
        leverage=leverage,
    )


def calculate_projected_margin_usage(
    account: AccountRiskSnapshot,
    portfolio: PortfolioRiskSnapshot,
    proposal: ProposedTrade,
    contract_size: Decimal = Decimal("100000.0"),
) -> MarginRiskSnapshot:
    """Project margin usage after a proposed trade using canonical evidence.

    Args:
        account: Canonical account-level risk snapshot.
        portfolio: Canonical portfolio-level risk snapshot.
        proposal: Candidate proposed trade.
        contract_size: Underlying contract size per standard lot.

    Returns:
        MarginRiskSnapshot: Projected margin, free margin, usage, and leverage
            after the proposed trade.
    """
    logger.info(
        f"Projecting margin usage for proposed trade on {proposal.symbol} "
        "from canonical snapshots."
    )
    leverage_cap = (
        account.leverage if account.leverage > Decimal("0.0") else Decimal("1.0")
    )
    proposed_margin = (
        (proposal.volume * contract_size * proposal.price) / leverage_cap
        if proposal.price > Decimal("0.0")
        else Decimal("0.0")
    )
    projected_margin = account.margin_used + proposed_margin
    equity = account.equity
    margin_usage = (
        projected_margin / equity if equity > Decimal("0.0") else Decimal("1.0")
    )
    free_margin = max(Decimal("0.0"), equity - projected_margin)
    logger.debug(
        f"Projected margin usage snapshot: projected_margin={projected_margin}, "
        f"usage={margin_usage}."
    )
    _ = portfolio
    return MarginRiskSnapshot(
        projected_margin=projected_margin,
        free_margin=free_margin,
        margin_usage=margin_usage,
        leverage=account.leverage,
    )


def calculate_free_margin_after_reservations(
    account: AccountRiskSnapshot,
    pending: Sequence[PendingOrderRiskSnapshot],
    inflight: Sequence[PendingOrderRiskSnapshot],
) -> Decimal:
    """Reserve pending and in-flight order exposure from account free margin.

    Args:
        account: Canonical account-level risk snapshot.
        pending: Pending order exposure snapshots.
        inflight: Currently executing (in-flight) order exposure snapshots.

    Returns:
        Decimal: Free margin remaining after reservations.
    """
    logger.info(
        f"Reserving free margin for {len(pending)} pending and "
        f"{len(inflight)} in-flight orders."
    )
    reserved = sum((o.exposure for o in pending), Decimal("0.0")) + sum(
        (o.exposure for o in inflight), Decimal("0.0")
    )
    remaining = max(Decimal("0.0"), account.free_margin - reserved)
    logger.debug(f"Free margin after reservations: {remaining}.")
    return remaining


def check_margin_limits(
    snapshot: MarginRiskSnapshot, policy: EffectiveRiskPolicy
) -> tuple[LimitResult, ...]:
    """Check a margin snapshot against account and portfolio policy caps.

    Args:
        snapshot: Calculated margin risk snapshot.
        policy: Resolved effective risk policy providing threshold configuration.

    Returns:
        tuple[LimitResult, ...]: Margin utilization and leverage limit results.
    """
    logger.info("Checking margin snapshot against effective policy caps.")
    config = policy.resolved_config
    results: list[LimitResult] = []

    if snapshot.margin_usage > config.max_margin_utilization_pct:
        results.append(
            LimitResult(
                limit_name="margin_limit",
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.MARGIN_BREACH,
                message=(
                    f"Margin utilization limit breached: "
                    f"{snapshot.margin_usage:.2%} > "
                    f"{config.max_margin_utilization_pct:.2%}."
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                details={"margin_usage": float(snapshot.margin_usage)},
            )
        )
    else:
        results.append(
            LimitResult(
                limit_name="margin_limit",
                status=RiskDecisionStatus.APPROVE,
                reason_code=RiskReasonCode.OK,
                message="Margin utilization is within policy caps.",
                severity=RiskSeverity.INFO,
                breached=False,
                details={"margin_usage": float(snapshot.margin_usage)},
            )
        )

    if snapshot.leverage > config.max_effective_leverage:
        results.append(
            LimitResult(
                limit_name="leverage_limit",
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.LEVERAGE_BREACH,
                message=(
                    f"Effective leverage limit breached: {snapshot.leverage:.2f} > "
                    f"{config.max_effective_leverage:.2f}."
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
                details={"leverage": float(snapshot.leverage)},
            )
        )
    else:
        results.append(
            LimitResult(
                limit_name="leverage_limit",
                status=RiskDecisionStatus.APPROVE,
                reason_code=RiskReasonCode.OK,
                message="Effective leverage is within policy caps.",
                severity=RiskSeverity.INFO,
                breached=False,
                details={"leverage": float(snapshot.leverage)},
            )
        )

    logger.debug(f"check_margin_limits produced {len(results)} results.")
    return tuple(results)
