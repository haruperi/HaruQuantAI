"""Stress scenario registry.

Manages the registration, validation, and retrieval of default
and custom stress scenarios.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from decimal import Decimal
from typing import Any, cast

from app.services.risk.stress.contracts import StressScenario
from app.utils.errors import ValidationError
from app.utils.logger import logger


class StressScenarioRegistry:
    """Immutable validated set of approved scenarios with deterministic lookup order.

    Attributes:
        scenarios: Dictionary mapping scenario IDs to StressScenario contracts.
    """

    def __init__(self, scenarios: Mapping[str, Any] | None = None) -> None:
        """Initialize the scenario registry.

        Args:
            scenarios: Optional initial mapping of scenario ID to StressScenario.
        """
        self.scenarios: dict[str, Any] = (
            dict(scenarios) if scenarios is not None else {}
        )
        logger.debug(
            f"StressScenarioRegistry instantiated with {len(self.scenarios)} scenarios."
        )

    def register_scenario(
        self, name: str, evaluator: Any  # noqa: ANN401
    ) -> None:
        """Legacy compatibility helper to register scenario in-place.

        Args:
            name: Scenario unique identifier name.
            evaluator: Evaluator object or StressScenario contract.
        """
        if not name.startswith("Scenario_") or name == "Scenario_0":
            logger.debug(f"Legacy register_scenario called for '{name}'.")
        self.scenarios[name] = evaluator

    def evaluate_portfolio(
        self,
        portfolio_state: Any,  # noqa: ANN401
        proposed_trade: Any,  # noqa: ANN401
        market_context: dict[str, Any],
        config: Any,  # noqa: ANN401
    ) -> list[Any]:
        """Legacy compatibility helper to evaluate all scenarios in registry.

        Args:
            portfolio_state: PortfolioState snapshot.
            proposed_trade: Candidate ProposedTrade.
            market_context: Quote/market details dictionary.
            config: Active RiskConfig profile.

        Returns:
            list[StressScenarioResult]: List of evaluated scenario results.
        """
        logger.debug("Legacy evaluate_portfolio on registry called.")
        from app.services.risk.policy.contracts import EffectiveRiskPolicy
        from app.services.risk.stress.contracts import StressContext
        from app.services.risk.stress.engine import evaluate_stress_scenarios

        context = StressContext.model_construct(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_context=market_context,
        )
        policy = EffectiveRiskPolicy.model_construct(
            policy_id="compat_policy",
            resolved_config=config,
            policy_hash="default",
        )
        summary = evaluate_stress_scenarios(context, self, policy)
        return summary.results


def register_stress_scenario(
    registry: StressScenarioRegistry, scenario: StressScenario
) -> StressScenarioRegistry:
    """Register a new stress scenario, returning a new registry.

    Performs duplicate detection and validation checks to prevent runtime conflicts.

    Args:
        registry: The current registry instance.
        scenario: The new scenario to register.

    Returns:
        StressScenarioRegistry: A new registry instance containing the scenario.

    Raises:
        ValidationError: If the scenario ID is a duplicate or invalid.
    """
    logger.debug(f"Attempting to register stress scenario: {scenario.scenario_id}")
    if scenario.scenario_id in registry.scenarios:
        msg = f"Duplicate scenario ID registered: {scenario.scenario_id}"
        logger.error(msg)
        raise ValidationError(msg)

    # Return a new registry to maintain purity
    new_scenarios = registry.scenarios.copy()
    new_scenarios[scenario.scenario_id] = scenario

    logger.info(
        f"Successfully registered stress scenario '{scenario.scenario_id}'."
    )
    return StressScenarioRegistry(scenarios=new_scenarios)


def get_stress_scenario(
    registry: StressScenarioRegistry, scenario_id: str
) -> StressScenario:
    """Retrieve a scenario deterministically or fail closed.

    Args:
        registry: The registry instance to search.
        scenario_id: The ID of the target scenario.

    Returns:
        StressScenario: The resolved scenario.

    Raises:
        ValidationError: If the scenario_id is not found.
    """
    logger.debug(f"Looking up scenario ID: {scenario_id}")
    if scenario_id not in registry.scenarios:
        msg = f"Stress scenario ID '{scenario_id}' not found in registry."
        logger.error(msg)
        raise ValidationError(msg)

    scenario = registry.scenarios[scenario_id]
    logger.debug(f"Successfully retrieved scenario: {scenario_id}")
    return cast("StressScenario", scenario)


def build_default_stress_registry() -> StressScenarioRegistry:
    """Build and return a pre-loaded stress testing scenario registry.

    Contains the 13 default macro and execution scenarios.

    Returns:
        StressScenarioRegistry: Registry initialized with default scenarios.
    """
    logger.info("Building default stress scenarios registry.")
    registry = StressScenarioRegistry()

    # 1. USD Shock Up
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="USD Shock Up",
            name="USD Shock Up",
            is_usd_shock=True,
            usd_shock_direction="up",
        ),
    )

    # 2. USD Shock Down
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="USD Shock Down",
            name="USD Shock Down",
            is_usd_shock=True,
            usd_shock_direction="down",
        ),
    )

    # 3. JPY Risk-Off
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="JPY Risk-Off",
            name="JPY Risk-Off",
            is_jpy_risk_off=True,
        ),
    )

    # 4. GBP Volatility Shock
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="GBP Volatility Shock",
            name="GBP Volatility Shock",
            is_gbp_volatility=True,
        ),
    )

    # 5. Spread Widening 5x
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Spread Widening 5x",
            name="Spread Widening 5x",
            spread_multiplier=Decimal("5.0"),
        ),
    )

    # 6. Slippage Shock 50 pips
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Slippage Shock 50 pips",
            name="Slippage Shock 50 pips",
        ),
    )

    # 7. Correlation to One
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Correlation to One",
            name="Correlation to One",
            is_correlation_to_one=True,
        ),
    )

    # 8. News Candle 5% Shock
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="News Candle 5% Shock",
            name="News Candle 5% Shock",
            is_news_candle=True,
        ),
    )

    # 9. Rollover Liquidity Shock
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Rollover Liquidity Shock",
            name="Rollover Liquidity Shock",
            spread_multiplier=Decimal("10.0"),
        ),
    )

    # 10. Margin Requirement Spike 2x
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Margin Requirement Spike 2x",
            name="Margin Requirement Spike 2x",
            margin_multiplier=Decimal("2.0"),
        ),
    )

    # 11. Platform Disconnect
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Platform Disconnect",
            name="Platform Disconnect",
            is_disconnect=True,
        ),
    )

    # 12. Stale Quote Check
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Stale Quote Check",
            name="Stale Quote Check",
            is_stale_quote_check=True,
        ),
    )

    # 13. Forced Liquidation Proximity
    registry = register_stress_scenario(
        registry,
        StressScenario(
            scenario_id="Forced Liquidation Proximity",
            name="Forced Liquidation Proximity",
            is_forced_liquidation_check=True,
        ),
    )

    logger.info("Successfully built default stress scenarios registry.")
    return registry


def validate_custom_scenario_definition(
    scenario: Mapping[str, Any]
) -> StressScenario:
    """Validate a custom scenario configuration without arbitrary code execution.

    Args:
        scenario: Configuration dictionary carrying 'name' and 'price_shocks'.

    Returns:
        StressScenario: The validated declarative scenario contract.

    Raises:
        ValidationError: If the configuration contains invalid types or values.
    """
    logger.debug(
        "Validating custom scenario definition against safety constraints."
    )
    name = scenario.get("name")
    if not isinstance(name, str) or not name.strip():
        msg = "Custom scenario config must have a non-empty string 'name'."
        logger.error(msg)
        raise ValidationError(msg)

    shocks_raw = scenario.get("price_shocks")
    if not isinstance(shocks_raw, dict):
        msg = "Custom scenario config must have a dictionary of 'price_shocks'."
        logger.error(msg)
        raise ValidationError(msg)

    price_shocks: dict[str, Decimal] = {}
    for sym, val in shocks_raw.items():
        if not isinstance(sym, str) or not sym.strip():
            msg = f"Invalid symbol key in custom scenario 'price_shocks': {sym}"
            logger.error(msg)
            raise ValidationError(msg)

        try:
            dec_val = Decimal(str(val))
        except Exception as e:
            msg = f"Invalid numeric shock value for '{sym}' in custom scenario: {val}"
            logger.error(msg)
            raise ValidationError(msg) from e

        # Limit price shock to a max of 100% (Decimal 1.0) for safety bounds
        if abs(dec_val) > Decimal("1.0"):
            msg = (
                f"Unsafe shock value for '{sym}' in custom scenario: "
                f"{dec_val} exceeds 100% boundary."
            )
            logger.error(msg)
            raise ValidationError(msg)

        price_shocks[sym] = dec_val

    # Convert name to a safe alphanumeric slug for scenario_id
    safe_id = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip().lower())
    scenario_id = f"custom_{safe_id}"

    logger.info(
        f"Custom scenario definition validated: {name} (ID: {scenario_id})"
    )
    return StressScenario(
        scenario_id=scenario_id,
        name=name,
        price_shocks=price_shocks,
    )
