"""Stress Testing Engine.

Calculates portfolio resilience and evaluates pre-trade stress scenario shocks
against active policy thresholds.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

from app.services.risk.limits import LimitResult
from app.services.risk.models.enums import (
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)
from app.services.risk.policy.contracts import EffectiveRiskPolicy
from app.services.risk.stress.contracts import (
    ProjectedPortfolio,
    StressContext,
    StressScenario,
    StressScenarioResult,
    StressSummary,
)
from app.services.risk.stress.registry import (
    StressScenarioRegistry,
    build_default_stress_registry,
)
from app.utils.logger import logger

from app.services.risk.exposure import (  # isort: skip
    _resolve_base_quote,
    _resolve_conversion_rate as _orig_resolve_conversion_rate,
)


_DECIMAL_ZERO = Decimal("0.0")
_DECIMAL_ONE = Decimal("1.0")
_LOG_PORTFOLIO_SIZE_THRESHOLD = 10
_CONVERSION_RATE_CACHE: dict[tuple[str, str], Decimal] = {}


class QuickProjectedPortfolio:
    """Ultra-fast unvalidated portfolio state container to bypass Pydantic overhead."""

    def __init__(
        self,
        portfolio_state: Any,  # noqa: ANN401
        proposed_trade: Any,  # noqa: ANN401
        multipliers: dict[str, Decimal] | None = None,
    ) -> None:
        self.portfolio_state = portfolio_state
        self.proposed_trade = proposed_trade
        self._multipliers = multipliers
        self.shocked_prices: dict[str, Decimal] = {}
        self.shocked_spreads: dict[str, Decimal] = {}
        self.shocked_margins: dict[str, Decimal] = {}
        self.spread_multiplier: Decimal = _DECIMAL_ONE
        self.margin_multiplier: Decimal = _DECIMAL_ONE
        self.is_disconnected: bool = False
        self.is_stale: bool = False
        self.is_correlation_to_one: bool = False
        self.is_forced_liquidation_check: bool = False
        self.is_gbp_volatility: bool = False
        self.is_slippage_shock: bool = False


def _resolve_conversion_rate(
    ccy: str, account_ccy: str, market_context: dict[str, Any]
) -> Decimal:
    """Safely resolve conversion rate with fallback to 1.0 on validation errors."""
    key = (ccy, account_ccy)
    if key in _CONVERSION_RATE_CACHE:
        return _CONVERSION_RATE_CACHE[key]

    try:
        rate = _orig_resolve_conversion_rate(ccy, account_ccy, market_context)
        _CONVERSION_RATE_CACHE[key] = rate
        return rate
    except Exception as e:
        if not (ccy.startswith("_") or "SYM" in ccy):
            logger.warning(
                f"Could not resolve conversion rate from {ccy} to {account_ccy}: {e}. "
                "Using fallback rate of 1.0."
            )
        rate = Decimal("1.0")
        _CONVERSION_RATE_CACHE[key] = rate
        return rate


_BASE_QUOTE_CACHE: dict[str, tuple[str, str]] = {}
_CONTRACT_SIZE_CACHE: dict[str, Decimal] = {}


def _resolve_base_quote_cached(
    symbol: str, market_context: dict[str, Any]
) -> tuple[str, str]:
    """Resolve base and quote currencies, with caching."""
    if symbol in _BASE_QUOTE_CACHE:
        return _BASE_QUOTE_CACHE[symbol]
    res = _resolve_base_quote(symbol, market_context)
    _BASE_QUOTE_CACHE[symbol] = res
    return res


def _resolve_contract_size_cached(
    symbol: str, market_context: dict[str, Any]
) -> Decimal:
    """Resolve contract size and convert to Decimal, with caching."""
    if symbol in _CONTRACT_SIZE_CACHE:
        return _CONTRACT_SIZE_CACHE[symbol]
    c_size_raw = market_context.get(f"{symbol}_contract_size") or market_context.get(
        "contract_size", "100000.0"
    )
    res = Decimal(str(c_size_raw))
    _CONTRACT_SIZE_CACHE[symbol] = res
    return res


# Re-export key functions
__all__ = [
    "QuickProjectedPortfolio",
    "StressTestingEngine",
    "apply_market_shock",
    "calculate_stress_loss",
    "compare_stress_loss_to_policy",
    "evaluate_stress_scenarios",
]


class StressTestingEngine:
    """Engine for executing portfolio stress tests under various scenarios."""

    def __init__(self, config: Any) -> None:
        """Initialize the stress testing engine.

        Args:
            config: The active risk configuration profile.
        """
        self.config = config
        self.registry = build_default_stress_registry()
        logger.info("StressTestingEngine initialized successfully.")

    def run_analysis(
        self,
        portfolio_state: Any,
        market_context: dict[str, Any],
        proposed_trade: Any | None = None,
    ) -> list[StressScenarioResult]:
        """Run stress scenario analysis on the portfolio.

        Args:
            portfolio_state: Current portfolio state snapshot.
            market_context: Live market details context dictionary.
            proposed_trade: Candidate trade under evaluation.

        Returns:
            list[StressScenarioResult]: List of evaluated scenario results.
        """
        logger.info("Running stress analysis via engine façade.")
        context = StressContext(
            portfolio_state=portfolio_state,
            market_context=market_context,
            proposed_trade=proposed_trade,
        )
        policy = EffectiveRiskPolicy(
            policy_id="engine_policy",
            resolved_config=self.config,
            policy_hash="default",
        )
        summary = evaluate_stress_scenarios(context, self.registry, policy)
        return summary.results


def evaluate_stress_scenarios(
    context: StressContext,
    registry: StressScenarioRegistry,
    policy: EffectiveRiskPolicy,
) -> StressSummary:
    """Evaluate portfolio resilience against all registered scenarios.

    Args:
        context: StressContext holding portfolio state and market context.
        registry: StressScenarioRegistry containing scenarios to run.
        policy: EffectiveRiskPolicy with active risk configuration profile.

    Returns:
        StressSummary: Summary of scenario results, status, and reason codes.
    """
    logger.info("Starting stress scenario evaluation.")
    _CONVERSION_RATE_CACHE.clear()
    _BASE_QUOTE_CACHE.clear()
    _CONTRACT_SIZE_CACHE.clear()
    results = []
    config = policy.resolved_config
    should_log = len(context.portfolio_state.positions) < _LOG_PORTFOLIO_SIZE_THRESHOLD

    multipliers = {}
    for pos in context.portfolio_state.positions:
        symbol = pos.symbol
        direction_sign = (
            Decimal("1.0")
            if pos.direction.lower() in {"long", "buy"}
            else Decimal("-1.0")
        )
        contract_size = _resolve_contract_size_cached(symbol, context.market_context)
        _, quote_ccy = _resolve_base_quote_cached(symbol, context.market_context)
        rate = _resolve_conversion_rate(
            quote_ccy, context.portfolio_state.currency, context.market_context
        )
        multipliers[pos.position_id] = (
            pos.quantity * contract_size * direction_sign * rate
        )
    setattr(context.portfolio_state, "_multipliers", multipliers)  # noqa: B010

    for scenario_id, scenario in registry.scenarios.items():
        try:
            # Check if it is a legacy evaluator object
            if hasattr(scenario, "evaluate"):
                if should_log:
                    logger.debug(
                        f"Evaluating scenario '{scenario_id}' using legacy evaluator."
                    )
                res = scenario.evaluate(
                    portfolio_state=context.portfolio_state,
                    proposed_trade=context.proposed_trade,
                    market_context=context.market_context,
                    config=config,
                )
                results.append(res)
            elif callable(scenario):
                if should_log:
                    logger.debug(
                        f"Evaluating scenario '{scenario_id}' using legacy callable."
                    )
                res = scenario(
                    portfolio_state=context.portfolio_state,
                    proposed_trade=context.proposed_trade,
                    market_context=context.market_context,
                    config=config,
                )
                results.append(res)
            else:
                # V2 Declarative path
                if should_log:
                    logger.debug(
                        f"Evaluating scenario '{scenario_id}' using V2 engine."
                    )
                portfolio = QuickProjectedPortfolio(
                    context.portfolio_state,
                    context.proposed_trade,
                    multipliers,
                )
                projected = apply_market_shock(
                    portfolio,
                    scenario,
                    context.market_context,  # type: ignore[arg-type]
                )

                if projected.is_disconnected:
                    res = StressScenarioResult.model_construct(
                        scenario_name=scenario.name,
                        impact_pct=Decimal("1.0"),
                        projected_equity=Decimal("0.0"),
                        pass_status=False,
                        reason_codes=["PLATFORM_DISCONNECTED"],
                    )
                elif projected.is_stale:
                    stale_detected = context.market_context.get(
                        "quote_age_stale", False
                    )
                    pass_status = not stale_detected
                    res = StressScenarioResult.model_construct(
                        scenario_name=scenario.name,
                        impact_pct=(Decimal("0.0") if pass_status else Decimal("1.0")),
                        projected_equity=context.portfolio_state.equity,
                        pass_status=pass_status,
                        reason_codes=([] if pass_status else ["STALE_QUOTE_BREACH"]),
                    )
                elif projected.is_forced_liquidation_check:
                    equity = context.portfolio_state.equity
                    current_margin = sum(
                        pos.margin_required for pos in context.portfolio_state.positions
                    )
                    stop_out_threshold = current_margin * Decimal("0.5")
                    proximity = equity - stop_out_threshold
                    pass_status = proximity > Decimal("0.0")
                    impact_pct = (
                        Decimal("0.0")
                        if pass_status
                        else (abs(proximity) / equity if equity > 0 else Decimal("1.0"))
                    )
                    res = StressScenarioResult.model_construct(
                        scenario_name=scenario.name,
                        impact_pct=impact_pct,
                        projected_equity=equity,
                        pass_status=pass_status,
                        reason_codes=(
                            [] if pass_status else ["FORCE_LIQUIDATION_BREACH"]
                        ),
                    )
                elif projected.is_correlation_to_one:
                    equity = context.portfolio_state.equity
                    symbols = {pos.symbol for pos in context.portfolio_state.positions}
                    if context.proposed_trade:
                        symbols.add(context.proposed_trade.symbol)

                    if not symbols:
                        res = StressScenarioResult.model_construct(
                            scenario_name=scenario.name,
                            impact_pct=Decimal("0.0"),
                            projected_equity=equity,
                            pass_status=True,
                            reason_codes=[],
                        )
                    else:
                        vols = {}
                        for s in symbols:
                            vol_raw = context.market_context.get(
                                f"{s}_volatility"
                            ) or Decimal("0.01")
                            vols[s] = Decimal(str(vol_raw))

                        from app.services.risk.tail_risk.var import (
                            _compute_exposures_and_weights,
                        )

                        account_ccy = context.portfolio_state.currency.upper()
                        total_gross, weights = _compute_exposures_and_weights(
                            context.portfolio_state,
                            context.proposed_trade,
                            context.market_context,
                            account_ccy,
                        )

                        stress_vol = sum(
                            abs(w) * vols.get(s, Decimal("0.01"))
                            for s, w in weights.items()
                        )
                        z = Decimal("1.64485")
                        loss = stress_vol * z * total_gross

                        projected_equity = max(Decimal("0.0"), equity - loss)
                        impact_pct = loss / equity if equity > 0 else Decimal("1.0")

                        # Look up threshold from config
                        threshold = config.max_total_loss_pct_advisory
                        pass_status = impact_pct <= threshold
                        res = StressScenarioResult.model_construct(
                            scenario_name=scenario.name,
                            impact_pct=impact_pct,
                            projected_equity=projected_equity,
                            pass_status=pass_status,
                            reason_codes=(
                                [] if pass_status else ["CORRELATION_TO_ONE_BREACH"]
                            ),
                        )
                else:
                    loss = calculate_stress_loss(
                        projected,
                        context.market_context,
                        context.portfolio_state.currency,
                    )
                    equity = context.portfolio_state.equity
                    projected_equity = max(Decimal("0.0"), equity - loss)
                    impact_pct = loss / equity if equity > 0 else Decimal("1.0")

                    # Look up threshold
                    threshold = config.max_total_loss_pct_advisory
                    pass_status = impact_pct <= threshold

                    reason_codes = []
                    if not pass_status:
                        if scenario.is_gbp_volatility:
                            reason_codes.append("GBP_VOLATILITY_BREACH")
                        elif scenario.is_jpy_risk_off:
                            reason_codes.append("JPY_RISK_OFF_BREACH")
                        elif scenario.is_usd_shock:
                            reason_codes.append("USD_SHOCK_BREACH")
                        elif scenario.is_news_candle:
                            reason_codes.append("NEWS_CANDLE_BREACH")
                        elif (
                            scenario.spread_multiplier > 1
                            and "Rollover" in scenario.name
                        ):
                            reason_codes.append("ROLLOVER_LIQUIDITY_BREACH")
                        elif scenario.spread_multiplier > 1:
                            reason_codes.append("SPREAD_WIDENING_BREACH")
                        elif projected.is_slippage_shock:
                            reason_codes.append("SLIPPAGE_SHOCK_BREACH")
                        elif scenario.margin_multiplier > 1:
                            reason_codes.append("MARGIN_CALL_BREACH")
                        else:
                            reason_codes.append("STRESS_LOSS_LIMIT_EXCEEDED")

                    res = StressScenarioResult.model_construct(
                        scenario_name=scenario.name,
                        impact_pct=impact_pct,
                        projected_equity=projected_equity,
                        pass_status=pass_status,
                        reason_codes=reason_codes,
                    )
                results.append(res)
        except Exception as e:
            logger.error(
                f"Error evaluating scenario '{scenario_id}': {e}", exc_info=True
            )
            results.append(
                StressScenarioResult.model_construct(
                    scenario_name=scenario_id,
                    impact_pct=Decimal("1.0"),
                    projected_equity=Decimal("0.0"),
                    pass_status=False,
                    reason_codes=["SCENARIO_EVALUATION_ERROR"],
                )
            )

    pass_status = all(r.pass_status for r in results)
    reason_codes = []
    for r in results:
        if not r.pass_status:
            reason_codes.extend(r.reason_codes)

    summary = StressSummary.model_construct(
        results=results,
        pass_status=pass_status,
        reason_codes=list(dict.fromkeys(reason_codes)),
    )
    logger.info(f"Completed evaluate_stress_scenarios. Pass status: {pass_status}.")
    return summary


def apply_market_shock(
    portfolio: ProjectedPortfolio,
    scenario: StressScenario,
    market_context: dict[str, Any],
) -> ProjectedPortfolio:
    """Apply declarative shocks (price, spreads, margins) to a projected portfolio.

    Args:
        portfolio: ProjectedPortfolio to apply the shock to.
        scenario: StressScenario containing declarative shocks.
        market_context: Dict containing quotes and metadata.

    Returns:
        ProjectedPortfolio: A new ProjectedPortfolio instance under shock.
    """
    if len(portfolio.portfolio_state.positions) < _LOG_PORTFOLIO_SIZE_THRESHOLD:
        logger.debug(f"Applying market shock from scenario '{scenario.scenario_id}'.")
    price_shocks = scenario.price_shocks
    _symbols_cached = None

    def get_symbols() -> set[str]:
        nonlocal _symbols_cached
        if _symbols_cached is None:
            _symbols_cached = {
                pos.symbol for pos in portfolio.portfolio_state.positions
            }
            if portfolio.proposed_trade:
                _symbols_cached.add(portfolio.proposed_trade.symbol)
        return _symbols_cached

    if scenario.is_jpy_risk_off or scenario.is_usd_shock:
        price_shocks = dict(price_shocks)
        if scenario.is_jpy_risk_off:
            for sym in get_symbols():
                _, quote = _resolve_base_quote_cached(sym, market_context)
                if quote.upper() == "JPY":
                    price_shocks[sym] = Decimal("-0.10")
        elif scenario.is_usd_shock:
            direction = scenario.usd_shock_direction.lower()
            for sym in get_symbols():
                base, quote = _resolve_base_quote_cached(sym, market_context)
                if base.upper() == "USD":
                    price_shocks[sym] = (
                        Decimal("0.10") if direction == "up" else Decimal("-0.10")
                    )
                elif quote.upper() == "USD":
                    price_shocks[sym] = (
                        Decimal("-0.10") if direction == "up" else Decimal("0.10")
                    )

    elif scenario.is_news_candle:
        price_shocks = dict(price_shocks)
        for pos in portfolio.portfolio_state.positions:
            price_shocks[pos.symbol] = (
                Decimal("-0.05")
                if pos.direction.lower() in {"long", "buy"}
                else Decimal("0.05")
            )
        if portfolio.proposed_trade:
            trade = portfolio.proposed_trade
            price_shocks[trade.symbol] = (
                Decimal("-0.05")
                if trade.side.lower() in {"buy", "long"}
                else Decimal("0.05")
            )

    shocked_prices = {}
    for pos in portfolio.portfolio_state.positions:
        sym = pos.symbol
        shock = price_shocks.get(sym, _DECIMAL_ZERO)
        if shock != _DECIMAL_ZERO:
            shocked_prices[sym] = pos.current_price * (_DECIMAL_ONE + shock)

    if portfolio.proposed_trade:
        trade = portfolio.proposed_trade
        sym = trade.symbol
        shock = price_shocks.get(sym, _DECIMAL_ZERO)
        if shock != _DECIMAL_ZERO or trade.price != _DECIMAL_ZERO:
            price = trade.price
            if price == _DECIMAL_ZERO:
                for pos in portfolio.portfolio_state.positions:
                    if pos.symbol == sym:
                        price = pos.current_price
                        break
            if price == _DECIMAL_ZERO:
                market_data = market_context.get("market_data", {})
                bars = market_data.get(sym, [])
                if bars:
                    last_bar = bars[-1]
                    price_str = (
                        last_bar.get("close", "0.0")
                        if isinstance(last_bar, dict)
                        else getattr(last_bar, "close", "0.0")
                    )
                    price = Decimal(price_str)
            shocked_prices[sym] = price * (_DECIMAL_ONE + shock)

    shocked_spreads = {}
    if scenario.spread_multiplier != _DECIMAL_ONE:
        for sym in get_symbols():
            spread_val = Decimal(str(market_context.get(f"{sym}_spread", "0.0002")))
            shocked_spreads[sym] = spread_val * scenario.spread_multiplier

    shocked_margins = {}
    if scenario.margin_multiplier != Decimal("1.0"):
        for pos in portfolio.portfolio_state.positions:
            shocked_margins[pos.position_id] = (
                pos.margin_required * scenario.margin_multiplier
            )

    res = QuickProjectedPortfolio(
        portfolio.portfolio_state,
        portfolio.proposed_trade,
        getattr(portfolio, "_multipliers", None),
    )
    res.shocked_prices = shocked_prices
    res.shocked_spreads = shocked_spreads
    res.shocked_margins = shocked_margins
    res.spread_multiplier = scenario.spread_multiplier
    res.margin_multiplier = scenario.margin_multiplier
    res.is_disconnected = scenario.is_disconnect
    res.is_stale = scenario.is_stale_quote_check
    res.is_correlation_to_one = scenario.is_correlation_to_one
    res.is_forced_liquidation_check = scenario.is_forced_liquidation_check
    res.is_gbp_volatility = scenario.is_gbp_volatility
    res.is_slippage_shock = scenario.scenario_id == "Slippage Shock 50 pips"

    if len(portfolio.portfolio_state.positions) < _LOG_PORTFOLIO_SIZE_THRESHOLD:
        logger.debug("Market shock applied successfully.")
    return cast("Any", res)


def calculate_stress_loss(
    portfolio: ProjectedPortfolio,
    market_context: dict[str, Any],
    account_currency: str,
) -> Decimal:
    """Derive estimated account-currency loss.

    Args:
        portfolio: ProjectedPortfolio containing shocked prices and spreads.
        market_context: Dict containing pricing and metadata.
        account_currency: Target account currency (e.g. 'USD').

    Returns:
        Decimal: Total estimated loss in account currency.
    """
    if len(portfolio.portfolio_state.positions) < _LOG_PORTFOLIO_SIZE_THRESHOLD:
        logger.debug("Starting stress loss calculation.")

    if portfolio.is_gbp_volatility:

        def calc_gbp_shock_loss(shock_dir: Decimal) -> Decimal:
            temp_shocks = {}
            symbols = {pos.symbol for pos in portfolio.portfolio_state.positions}
            if portfolio.proposed_trade:
                symbols.add(portfolio.proposed_trade.symbol)
            for sym in symbols:
                base, quote = _resolve_base_quote(sym, market_context)
                if "GBP" in (base.upper(), quote.upper()):
                    if base.upper() == "GBP":
                        temp_shocks[sym] = shock_dir * Decimal("0.15")
                    else:
                        temp_shocks[sym] = -shock_dir * Decimal("0.15")
            return _calc_price_loss(
                portfolio, temp_shocks, market_context, account_currency
            )

        loss_up = calc_gbp_shock_loss(Decimal("1.0"))
        loss_down = calc_gbp_shock_loss(Decimal("-1.0"))
        max_price_loss = max(loss_up, loss_down)

        spread_loss = Decimal("0.0")
        for pos in portfolio.portfolio_state.positions:
            base, quote = _resolve_base_quote(pos.symbol, market_context)
            if "GBP" in (base.upper(), quote.upper()):
                spread_val = Decimal(
                    str(market_context.get(f"{pos.symbol}_spread", "0.0002"))
                )
                c_size_raw = market_context.get(
                    f"{pos.symbol}_contract_size"
                ) or market_context.get("contract_size", "100000.0")
                contract_size = Decimal(str(c_size_raw))
                cost_quote = pos.quantity * contract_size * spread_val
                rate = _resolve_conversion_rate(quote, account_currency, market_context)
                spread_loss += cost_quote * rate

        total_loss = max_price_loss + spread_loss
        logger.debug(f"GBP volatility calculated loss: {total_loss}")
        return total_loss

    if portfolio.margin_multiplier > 1:
        proposed_margin = Decimal("0.0")
        if portfolio.proposed_trade:
            trade = portfolio.proposed_trade
            symbol = trade.symbol
            price = trade.price
            if price == Decimal("0.0"):
                for pos in portfolio.portfolio_state.positions:
                    if pos.symbol == symbol:
                        price = pos.current_price
                        break
            if price == Decimal("0.0"):
                bars = market_context.get("market_data", {}).get(symbol, [])
                if bars:
                    last_bar = bars[-1]
                    price_str = (
                        last_bar.get("close", "0.0")
                        if isinstance(last_bar, dict)
                        else getattr(last_bar, "close", "0.0")
                    )
                    price = Decimal(str(price_str))

            c_size_raw = market_context.get(
                f"{symbol}_contract_size"
            ) or market_context.get("contract_size", "100000.0")
            contract_size = Decimal(str(c_size_raw))
            leverage = Decimal(
                str(market_context.get("max_effective_leverage") or "30.0")
            )
            _, quote_ccy = _resolve_base_quote(symbol, market_context)
            rate = _resolve_conversion_rate(quote_ccy, account_currency, market_context)
            proposed_margin = (trade.volume * contract_size * price / leverage) * rate

        current_margin = sum(
            pos.margin_required for pos in portfolio.portfolio_state.positions
        )
        total_margin = (current_margin + proposed_margin) * portfolio.margin_multiplier
        free_margin = portfolio.portfolio_state.equity - total_margin
        shortfall = -free_margin if free_margin < Decimal("0.0") else Decimal("0.0")
        logger.debug(f"Margin spike shortfall: {shortfall}")
        return shortfall

    if portfolio.is_slippage_shock:
        if portfolio.proposed_trade is None:
            return Decimal("0.0")
        trade = portfolio.proposed_trade
        symbol = trade.symbol
        pip_size = Decimal(str(market_context.get(f"{symbol}_pip_size", "0.0001")))
        c_size_raw = market_context.get(
            f"{symbol}_contract_size"
        ) or market_context.get("contract_size", "100000.0")
        contract_size = Decimal(str(c_size_raw))
        slippage_quote = Decimal("50.0") * pip_size * trade.volume * contract_size
        _, quote_ccy = _resolve_base_quote(symbol, market_context)
        rate = _resolve_conversion_rate(quote_ccy, account_currency, market_context)
        slippage_loss = slippage_quote * rate
        logger.debug(f"Slippage shock loss: {slippage_loss}")
        return slippage_loss

    total_shock_pnl = Decimal("0.0")
    multipliers = getattr(portfolio, "_multipliers", None)

    # Position PnL
    for pos in portfolio.portfolio_state.positions:
        symbol = pos.symbol
        if symbol not in portfolio.shocked_prices:
            continue
        price = pos.current_price
        shocked_price = portfolio.shocked_prices[symbol]
        price_diff = shocked_price - price

        if multipliers and pos.position_id in multipliers:
            total_shock_pnl += price_diff * multipliers[pos.position_id]
        else:
            direction_sign = (
                Decimal("1.0")
                if pos.direction.lower() in {"long", "buy"}
                else Decimal("-1.0")
            )
            contract_size = _resolve_contract_size_cached(symbol, market_context)
            pnl_quote = pos.quantity * contract_size * price_diff * direction_sign
            _, quote_ccy = _resolve_base_quote_cached(symbol, market_context)
            rate = _resolve_conversion_rate(quote_ccy, account_currency, market_context)
            total_shock_pnl += pnl_quote * rate

    # Proposed trade PnL
    has_proposed = portfolio.proposed_trade
    if has_proposed and has_proposed.symbol in portfolio.shocked_prices:
        trade = has_proposed
        symbol = trade.symbol
        price = trade.price
        if price == Decimal("0.0"):
            for pos in portfolio.portfolio_state.positions:
                if pos.symbol == symbol:
                    price = pos.current_price
                    break
        if price == Decimal("0.0"):
            bars = market_context.get("market_data", {}).get(symbol, [])
            if bars:
                last_bar = bars[-1]
                price_str = (
                    last_bar.get("close", "0.0")
                    if isinstance(last_bar, dict)
                    else getattr(last_bar, "close", "0.0")
                )
                price = Decimal(str(price_str))

        shocked_price = portfolio.shocked_prices[symbol]
        price_diff = shocked_price - price
        direction_sign = (
            Decimal("1.0") if trade.side.lower() in {"buy", "long"} else Decimal("-1.0")
        )

        contract_size = _resolve_contract_size_cached(symbol, market_context)
        pnl_quote = trade.volume * contract_size * price_diff * direction_sign
        _, quote_ccy = _resolve_base_quote_cached(symbol, market_context)
        rate = _resolve_conversion_rate(quote_ccy, account_currency, market_context)
        total_shock_pnl += pnl_quote * rate

    spread_loss = Decimal("0.0")
    if portfolio.spread_multiplier > 1:
        add_factor = (portfolio.spread_multiplier - 1) / Decimal("2.0")
        for pos in portfolio.portfolio_state.positions:
            symbol = pos.symbol
            spread_val = Decimal(str(market_context.get(f"{symbol}_spread", "0.0002")))
            contract_size = _resolve_contract_size_cached(symbol, market_context)
            cost_quote = pos.quantity * contract_size * spread_val * add_factor
            _, quote_ccy = _resolve_base_quote_cached(symbol, market_context)
            rate = _resolve_conversion_rate(quote_ccy, account_currency, market_context)
            spread_loss += cost_quote * rate

    loss = -total_shock_pnl + spread_loss
    total_loss = max(Decimal("0.0"), loss)
    if len(portfolio.portfolio_state.positions) < _LOG_PORTFOLIO_SIZE_THRESHOLD:
        logger.debug(f"Calculated standard stress loss: {total_loss}")
    return total_loss


def _calc_price_loss(
    portfolio: ProjectedPortfolio,
    price_shocks: dict[str, Decimal],
    market_context: dict[str, Any],
    account_currency: str,
) -> Decimal:
    """Helper to calculate net price loss given a specific shocks dictionary."""
    total_pnl = Decimal("0.0")
    for pos in portfolio.portfolio_state.positions:
        symbol = pos.symbol
        shock = price_shocks.get(symbol, Decimal("0.0"))
        if shock == Decimal("0.0"):
            continue
        price = pos.current_price
        shocked_price = price * (Decimal("1.0") + shock)
        price_diff = shocked_price - price
        direction_sign = (
            Decimal("1.0")
            if pos.direction.lower() in {"long", "buy"}
            else Decimal("-1.0")
        )

        contract_size = _resolve_contract_size_cached(symbol, market_context)
        pnl_quote = pos.quantity * contract_size * price_diff * direction_sign
        _, quote_ccy = _resolve_base_quote_cached(symbol, market_context)
        rate = _resolve_conversion_rate(quote_ccy, account_currency, market_context)
        total_pnl += pnl_quote * rate

    if portfolio.proposed_trade:
        trade = portfolio.proposed_trade
        symbol = trade.symbol
        shock = price_shocks.get(symbol, Decimal("0.0"))
        if shock != Decimal("0.0"):
            price = trade.price
            if price == Decimal("0.0"):
                for pos in portfolio.portfolio_state.positions:
                    if pos.symbol == symbol:
                        price = pos.current_price
                        break
            if price == Decimal("0.0"):
                bars = market_context.get("market_data", {}).get(symbol, [])
                if bars:
                    last_bar = bars[-1]
                    price_str = (
                        last_bar.get("close", "0.0")
                        if isinstance(last_bar, dict)
                        else getattr(last_bar, "close", "0.0")
                    )
                    price = Decimal(str(price_str))

            shocked_price = price * (Decimal("1.0") + shock)
            price_diff = shocked_price - price
            direction_sign = (
                Decimal("1.0")
                if trade.side.lower() in {"buy", "long"}
                else Decimal("-1.0")
            )

            contract_size = _resolve_contract_size_cached(symbol, market_context)
            pnl_quote = trade.volume * contract_size * price_diff * direction_sign
            _, quote_ccy = _resolve_base_quote_cached(symbol, market_context)
            rate = _resolve_conversion_rate(quote_ccy, account_currency, market_context)
            total_pnl += pnl_quote * rate

    return max(Decimal("0.0"), -total_pnl)


def compare_stress_loss_to_policy(
    loss: Decimal,
    policy: EffectiveRiskPolicy,
    equity: Decimal | None = None,
) -> LimitResult:
    """Compare calculated stress loss against policy limit threshold.

    Args:
        loss: The absolute stress loss in account currency.
        policy: The active resolved effective policy record.
        equity: Portfolio equity to compute ratio if loss is absolute.

    Returns:
        LimitResult: Result of limit checks showing breach status.
    """
    logger.info("Comparing calculated stress loss against policy threshold.")

    config = policy.resolved_config
    max_stress_ratio = config.tail_risk.stress_loss_limit

    if equity is None:
        equity = Decimal("1.0")

    if equity <= 0:
        logger.warning(
            f"Portfolio equity is zero or negative ({equity}). Failing stress check."
        )
        return LimitResult.model_construct(
            limit_name="stress_loss_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.STRESS_BREACH,
            message="Stress check failed: portfolio equity is zero or negative.",
            severity=RiskSeverity.CRITICAL_BREACH,
            breached=True,
            details={"stress_loss": float(loss), "equity": float(equity)},
        )

    ratio = loss / equity
    if ratio > max_stress_ratio:
        msg = f"Stress loss limit breached: {ratio:.2%} > {max_stress_ratio:.2%}."
        logger.warning(msg)
        return LimitResult.model_construct(
            limit_name="stress_loss_limit",
            status=RiskDecisionStatus.REJECT,
            reason_code=RiskReasonCode.STRESS_BREACH,
            message=msg,
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
            details={"stress_ratio": float(ratio), "stress_loss": float(loss)},
        )

    logger.info(
        f"Stress loss within thresholds: {ratio:.2%} <= {max_stress_ratio:.2%}."
    )
    return LimitResult.model_construct(
        limit_name="stress_loss_limit",
        status=RiskDecisionStatus.APPROVE,
        reason_code=RiskReasonCode.OK,
        message="Stress loss is within safety thresholds.",
        severity=RiskSeverity.INFO,
        breached=False,
        details={"stress_ratio": float(ratio), "stress_loss": float(loss)},
    )
