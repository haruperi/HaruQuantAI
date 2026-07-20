"""Stress testing engine package.

Provides declarative stress scenarios, registries, evaluation engines,
and compatibility wrappers for legacy integration.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.risk.models import StressScenarioResult
from app.services.risk.policy.contracts import EffectiveRiskPolicy
from app.services.risk.stress.contracts import (
    ProjectedPortfolio,
    StressContext,
    StressScenario,
    StressSummary,
)
from app.services.risk.stress.engine import (
    QuickProjectedPortfolio,
    StressTestingEngine,
    apply_market_shock,
    calculate_stress_loss,
    compare_stress_loss_to_policy,
    evaluate_stress_scenarios,
)
from app.services.risk.stress.registry import (
    StressScenarioRegistry,
    build_default_stress_registry,
    get_stress_scenario,
    register_stress_scenario,
    validate_custom_scenario_definition,
)

_DECIMAL_ZERO = Decimal("0.0")
_DECIMAL_ONE = Decimal("1.0")
from app.utils.logger import logger

# Re-export clean public APIs
__all__ = [
    "StressContext",
    "ProjectedPortfolio",
    "StressScenario",
    "StressSummary",
    "StressScenarioResult",
    "StressScenarioRegistry",
    "build_default_stress_registry",
    "register_stress_scenario",
    "get_stress_scenario",
    "validate_custom_scenario_definition",
    "StressTestingEngine",
    "evaluate_stress_scenarios",
    "apply_market_shock",
    "calculate_stress_loss",
    "compare_stress_loss_to_policy",
    # Legacy compat exports
    "PriceShockScenario",
    "USDShockScenario",
    "JPYRiskOffScenario",
    "GBPVolatilityScenario",
    "SpreadWideningScenario",
    "SlippageShockScenario",
    "CorrelationToOneScenario",
    "NewsCandleScenario",
    "RolloverLiquidityScenario",
    "MarginSpikeScenario",
    "PlatformDisconnectScenario",
    "StaleQuoteScenario",
    "ForcedLiquidationScenario",
    "build_default_scenario_registry",
    "validate_custom_scenario",
    "run_stress_scenario_analysis",
    "evaluate_usd_shock",
    "evaluate_jpy_risk_off_shock",
    "evaluate_spread_widening_shock",
    "evaluate_slippage_shock",
    "evaluate_correlation_to_one_shock",
    "evaluate_news_candle_shock",
    "evaluate_rollover_liquidity_shock",
    "evaluate_margin_spike_shock",
    "evaluate_platform_disconnect_shock",
]


# =====================================================================
# V1 Compatibility Wrappers & Helpers
# =====================================================================


def build_default_scenario_registry() -> StressScenarioRegistry:
    """Legacy alias for build_default_stress_registry."""
    logger.debug("Legacy build_default_scenario_registry called.")
    return build_default_stress_registry()


def validate_custom_scenario(scenario_dict: dict[str, Any]) -> StressScenario:
    """Legacy alias for validate_custom_scenario_definition."""
    logger.debug("Legacy validate_custom_scenario called.")
    return validate_custom_scenario_definition(scenario_dict)


def run_stress_scenario_analysis(
    portfolio_state: Any,
    market_context: dict[str, Any],
    config: Any,
    proposed_trade: Any | None = None,
) -> list[StressScenarioResult]:
    """Legacy helper to run default stress tests on a portfolio."""
    logger.info("Legacy run_stress_scenario_analysis wrapper called.")
    engine = StressTestingEngine(config)
    return engine.run_analysis(portfolio_state, market_context, proposed_trade)


def evaluate_usd_shock(
    portfolio_state: Any,
    proposed_trade: Any | None,
    market_context: dict[str, Any],
    config: Any,
    shock_direction: str = "up",
) -> StressScenarioResult:
    """Legacy helper to evaluate USD shock scenario."""
    logger.debug("Legacy evaluate_usd_shock called.")
    context = StressContext(
        portfolio_state=portfolio_state,
        market_context=market_context,
        proposed_trade=proposed_trade,
    )
    registry = StressScenarioRegistry()
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="USD Shock",
            name=f"USD Shock {shock_direction.capitalize()}",
            is_usd_shock=True,
            usd_shock_direction=shock_direction,
        ),
    )
    policy = EffectiveRiskPolicy(
        policy_id="wrapper_policy",
        resolved_config=config,
        policy_hash="default",
    )
    summary = evaluate_stress_scenarios(context, registry, policy)
    return summary.results[0]


def evaluate_jpy_risk_off_shock(
    portfolio_state: Any,
    proposed_trade: Any | None,
    market_context: dict[str, Any],
    config: Any,
) -> StressScenarioResult:
    """Legacy helper to evaluate JPY risk-off shock scenario."""
    logger.debug("Legacy evaluate_jpy_risk_off_shock called.")
    context = StressContext(
        portfolio_state=portfolio_state,
        market_context=market_context,
        proposed_trade=proposed_trade,
    )
    registry = StressScenarioRegistry()
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="JPY Risk-Off",
            name="JPY Risk-Off",
            is_jpy_risk_off=True,
        ),
    )
    policy = EffectiveRiskPolicy(
        policy_id="wrapper_policy",
        resolved_config=config,
        policy_hash="default",
    )
    summary = evaluate_stress_scenarios(context, registry, policy)
    return summary.results[0]


def evaluate_spread_widening_shock(
    portfolio_state: Any,
    proposed_trade: Any | None,
    market_context: dict[str, Any],
    config: Any,
) -> StressScenarioResult:
    """Legacy helper to evaluate spread widening shock scenario."""
    logger.debug("Legacy evaluate_spread_widening_shock called.")
    context = StressContext(
        portfolio_state=portfolio_state,
        market_context=market_context,
        proposed_trade=proposed_trade,
    )
    registry = StressScenarioRegistry()
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Spread Widening 5x",
            name="Spread Widening 5x",
            spread_multiplier=Decimal("5.0"),
        ),
    )
    policy = EffectiveRiskPolicy(
        policy_id="wrapper_policy",
        resolved_config=config,
        policy_hash="default",
    )
    summary = evaluate_stress_scenarios(context, registry, policy)
    return summary.results[0]


def evaluate_slippage_shock(
    portfolio_state: Any,
    proposed_trade: Any | None,
    market_context: dict[str, Any],
    config: Any,
) -> StressScenarioResult:
    """Legacy helper to evaluate slippage shock scenario."""
    logger.debug("Legacy evaluate_slippage_shock called.")
    context = StressContext(
        portfolio_state=portfolio_state,
        market_context=market_context,
        proposed_trade=proposed_trade,
    )
    registry = StressScenarioRegistry()
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Slippage Shock 50 pips",
            name="Slippage Shock 50 pips",
        ),
    )
    policy = EffectiveRiskPolicy(
        policy_id="wrapper_policy",
        resolved_config=config,
        policy_hash="default",
    )
    summary = evaluate_stress_scenarios(context, registry, policy)
    return summary.results[0]


def evaluate_correlation_to_one_shock(
    portfolio_state: Any,
    proposed_trade: Any | None,
    market_context: dict[str, Any],
    config: Any,
) -> StressScenarioResult:
    """Legacy helper to evaluate correlation collapse shock scenario."""
    logger.debug("Legacy evaluate_correlation_to_one_shock called.")
    context = StressContext(
        portfolio_state=portfolio_state,
        market_context=market_context,
        proposed_trade=proposed_trade,
    )
    registry = StressScenarioRegistry()
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Correlation to One",
            name="Correlation to One",
            is_correlation_to_one=True,
        ),
    )
    policy = EffectiveRiskPolicy(
        policy_id="wrapper_policy",
        resolved_config=config,
        policy_hash="default",
    )
    summary = evaluate_stress_scenarios(context, registry, policy)
    return summary.results[0]


def evaluate_news_candle_shock(
    portfolio_state: Any,
    proposed_trade: Any | None,
    market_context: dict[str, Any],
    config: Any,
) -> StressScenarioResult:
    """Legacy helper to evaluate news candle shock scenario."""
    logger.debug("Legacy evaluate_news_candle_shock called.")
    context = StressContext(
        portfolio_state=portfolio_state,
        market_context=market_context,
        proposed_trade=proposed_trade,
    )
    registry = StressScenarioRegistry()
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="News Candle 5% Shock",
            name="News Candle 5% Shock",
            is_news_candle=True,
        ),
    )
    policy = EffectiveRiskPolicy(
        policy_id="wrapper_policy",
        resolved_config=config,
        policy_hash="default",
    )
    summary = evaluate_stress_scenarios(context, registry, policy)
    return summary.results[0]


def evaluate_rollover_liquidity_shock(
    portfolio_state: Any,
    proposed_trade: Any | None,
    market_context: dict[str, Any],
    config: Any,
) -> StressScenarioResult:
    """Legacy helper to evaluate rollover liquidity shock scenario."""
    logger.debug("Legacy evaluate_rollover_liquidity_shock called.")
    context = StressContext(
        portfolio_state=portfolio_state,
        market_context=market_context,
        proposed_trade=proposed_trade,
    )
    registry = StressScenarioRegistry()
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Rollover Liquidity Shock",
            name="Rollover Liquidity Shock",
            spread_multiplier=Decimal("10.0"),
        ),
    )
    policy = EffectiveRiskPolicy(
        policy_id="wrapper_policy",
        resolved_config=config,
        policy_hash="default",
    )
    summary = evaluate_stress_scenarios(context, registry, policy)
    return summary.results[0]


def evaluate_margin_spike_shock(
    portfolio_state: Any,
    proposed_trade: Any | None,
    market_context: dict[str, Any],
    config: Any,
) -> StressScenarioResult:
    """Legacy helper to evaluate margin spike shock scenario."""
    logger.debug("Legacy evaluate_margin_spike_shock called.")
    context = StressContext(
        portfolio_state=portfolio_state,
        market_context=market_context,
        proposed_trade=proposed_trade,
    )
    registry = StressScenarioRegistry()
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Margin Requirement Spike 2x",
            name="Margin Requirement Spike 2x",
            margin_multiplier=Decimal("2.0"),
        ),
    )
    policy = EffectiveRiskPolicy(
        policy_id="wrapper_policy",
        resolved_config=config,
        policy_hash="default",
    )
    summary = evaluate_stress_scenarios(context, registry, policy)
    return summary.results[0]


def evaluate_platform_disconnect_shock(
    portfolio_state: Any,
    proposed_trade: Any | None,
    market_context: dict[str, Any],
    config: Any,
) -> StressScenarioResult:
    """Legacy helper to evaluate platform disconnect shock scenario."""
    logger.debug("Legacy evaluate_platform_disconnect_shock called.")
    context = StressContext(
        portfolio_state=portfolio_state,
        market_context=market_context,
        proposed_trade=proposed_trade,
    )
    registry = StressScenarioRegistry()
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Platform Disconnect",
            name="Platform Disconnect",
            is_disconnect=True,
        ),
    )
    policy = EffectiveRiskPolicy(
        policy_id="wrapper_policy",
        resolved_config=config,
        policy_hash="default",
    )
    summary = evaluate_stress_scenarios(context, registry, policy)
    return summary.results[0]


# =====================================================================
# V1 Scenario Class Adaptors (for test and client compatibility)
# =====================================================================


class PriceShockScenario:
    """Legacy adaptor class for PriceShockScenario."""

    def __init__(self, name: str, price_shocks: dict[str, Decimal]) -> None:
        """Initialize scenario details."""
        self.name = name
        self.price_shocks = price_shocks

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        if len(portfolio_state.positions) < 10:
            logger.debug(
                f"PriceShockScenario legacy adaptor evaluate called for '{self.name}'."
            )
        portfolio = QuickProjectedPortfolio(
            portfolio_state,
            proposed_trade,
            getattr(portfolio_state, "_multipliers", None),
        )
        scenario = StressScenario.model_construct(
            scenario_id=self.name,
            name=self.name,
            price_shocks=self.price_shocks,
            spread_multiplier=Decimal("1.0"),
            margin_multiplier=Decimal("1.0"),
            is_disconnect=False,
            is_stale_quote_check=False,
            is_correlation_to_one=False,
            is_forced_liquidation_check=False,
            is_gbp_volatility=False,
            is_jpy_risk_off=False,
            is_usd_shock=False,
            usd_shock_direction="up",
            is_news_candle=False,
        )
        projected = apply_market_shock(
            portfolio,
            scenario,
            market_context,  # type: ignore[arg-type]
        )
        loss = calculate_stress_loss(
            projected, market_context, portfolio_state.currency
        )
        equity = portfolio_state.equity
        projected_equity = max(Decimal("0.0"), equity - loss)
        impact_pct = loss / equity if equity > Decimal("0.0") else Decimal("1.0")

        threshold = config.max_total_loss_pct_advisory
        pass_status = impact_pct <= threshold
        reason_codes = [] if pass_status else ["STRESS_LOSS_LIMIT_EXCEEDED"]

        return StressScenarioResult.model_construct(
            scenario_name=self.name,
            impact_pct=impact_pct,
            projected_equity=projected_equity,
            pass_status=pass_status,
            reason_codes=reason_codes,
        )


class USDShockScenario:
    """Legacy adaptor class for USDShockScenario."""

    def __init__(self, shock_direction: str = "up") -> None:
        """Initialize scenario details."""
        self.name = f"USD Shock {shock_direction.capitalize()}"
        self.direction = shock_direction

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("USDShockScenario legacy adaptor evaluate called.")
        return evaluate_usd_shock(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_context=market_context,
            config=config,
            shock_direction=self.direction,
        )


class JPYRiskOffScenario:
    """Legacy adaptor class for JPYRiskOffScenario."""

    def __init__(self) -> None:
        """Initialize scenario details."""
        self.name = "JPY Risk-Off"

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("JPYRiskOffScenario legacy adaptor evaluate called.")
        return evaluate_jpy_risk_off_shock(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_context=market_context,
            config=config,
        )


class GBPVolatilityScenario:
    """Legacy adaptor class for GBPVolatilityScenario."""

    def __init__(self) -> None:
        """Initialize scenario details."""
        self.name = "GBP Volatility Shock"

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("GBPVolatilityScenario legacy adaptor evaluate called.")
        context = StressContext(
            portfolio_state=portfolio_state,
            market_context=market_context,
            proposed_trade=proposed_trade,
        )
        registry = StressScenarioRegistry()
        registry = register_stress_scenario(
            registry,
            StressScenario(
                scenario_id="GBP Volatility Shock",
                name="GBP Volatility Shock",
                is_gbp_volatility=True,
            ),
        )
        policy = EffectiveRiskPolicy(
            policy_id="wrapper_policy",
            resolved_config=config,
            policy_hash="default",
        )
        summary = evaluate_stress_scenarios(context, registry, policy)
        return summary.results[0]


class SpreadWideningScenario:
    """Legacy adaptor class for SpreadWideningScenario."""

    def __init__(self) -> None:
        """Initialize scenario details."""
        self.name = "Spread Widening 5x"

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("SpreadWideningScenario legacy adaptor evaluate called.")
        return evaluate_spread_widening_shock(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_context=market_context,
            config=config,
        )


class SlippageShockScenario:
    """Legacy adaptor class for SlippageShockScenario."""

    def __init__(self) -> None:
        """Initialize scenario details."""
        self.name = "Slippage Shock 50 pips"

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("SlippageShockScenario legacy adaptor evaluate called.")
        return evaluate_slippage_shock(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_context=market_context,
            config=config,
        )


class CorrelationToOneScenario:
    """Legacy adaptor class for CorrelationToOneScenario."""

    def __init__(self) -> None:
        """Initialize scenario details."""
        self.name = "Correlation to One"

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("CorrelationToOneScenario legacy adaptor evaluate called.")
        return evaluate_correlation_to_one_shock(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_context=market_context,
            config=config,
        )


class NewsCandleScenario:
    """Legacy adaptor class for NewsCandleScenario."""

    def __init__(self) -> None:
        """Initialize scenario details."""
        self.name = "News Candle 5% Shock"

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("NewsCandleScenario legacy adaptor evaluate called.")
        return evaluate_news_candle_shock(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_context=market_context,
            config=config,
        )


class RolloverLiquidityScenario:
    """Legacy adaptor class for RolloverLiquidityScenario."""

    def __init__(self) -> None:
        """Initialize scenario details."""
        self.name = "Rollover Liquidity Shock"

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("RolloverLiquidityScenario legacy adaptor evaluate called.")
        return evaluate_rollover_liquidity_shock(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_context=market_context,
            config=config,
        )


class MarginSpikeScenario:
    """Legacy adaptor class for MarginSpikeScenario."""

    def __init__(self) -> None:
        """Initialize scenario details."""
        self.name = "Margin Requirement Spike 2x"

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("MarginSpikeScenario legacy adaptor evaluate called.")
        return evaluate_margin_spike_shock(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_context=market_context,
            config=config,
        )


class PlatformDisconnectScenario:
    """Legacy adaptor class for PlatformDisconnectScenario."""

    def __init__(self) -> None:
        """Initialize scenario details."""
        self.name = "Platform Disconnect"

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("PlatformDisconnectScenario legacy adaptor evaluate called.")
        return evaluate_platform_disconnect_shock(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_context=market_context,
            config=config,
        )


class StaleQuoteScenario:
    """Legacy adaptor class for StaleQuoteScenario."""

    def __init__(self) -> None:
        """Initialize scenario details."""
        self.name = "Stale Quote Check"

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("StaleQuoteScenario legacy adaptor evaluate called.")
        context = StressContext(
            portfolio_state=portfolio_state,
            market_context=market_context,
            proposed_trade=proposed_trade,
        )
        registry = StressScenarioRegistry()
        registry = register_stress_scenario(
            registry,
            StressScenario(
                scenario_id="Stale Quote Check",
                name="Stale Quote Check",
                is_stale_quote_check=True,
            ),
        )
        policy = EffectiveRiskPolicy(
            policy_id="wrapper_policy",
            resolved_config=config,
            policy_hash="default",
        )
        summary = evaluate_stress_scenarios(context, registry, policy)
        return summary.results[0]


class ForcedLiquidationScenario:
    """Legacy adaptor class for ForcedLiquidationScenario."""

    def __init__(self) -> None:
        """Initialize scenario details."""
        self.name = "Forced Liquidation Proximity"

    def evaluate(
        self,
        portfolio_state: Any,
        proposed_trade: Any,
        market_context: dict[str, Any],
        config: Any,
    ) -> StressScenarioResult:
        """Map legacy evaluation request to V2 engine execution."""
        logger.debug("ForcedLiquidationScenario legacy adaptor evaluate called.")
        context = StressContext(
            portfolio_state=portfolio_state,
            market_context=market_context,
            proposed_trade=proposed_trade,
        )
        registry = StressScenarioRegistry()
        registry = register_stress_scenario(
            registry,
            StressScenario(
                scenario_id="Forced Liquidation Proximity",
                name="Forced Liquidation Proximity",
                is_forced_liquidation_check=True,
            ),
        )
        policy = EffectiveRiskPolicy(
            policy_id="wrapper_policy",
            resolved_config=config,
            policy_hash="default",
        )
        summary = evaluate_stress_scenarios(context, registry, policy)
        return summary.results[0]


# Initialize log on import
logger.info("Stress package initialized successfully.")
