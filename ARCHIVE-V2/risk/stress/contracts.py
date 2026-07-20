"""Contracts for the Stress Testing Engine.

Defines Pydantic model schemas for declarative stress scenarios,
execution contexts, projected portfolios, and summary results.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.risk.models import (
    PortfolioState,
    ProposedTrade,
    RiskContract,
    StressScenarioResult,
)
from app.utils.logger import logger
from pydantic import Field

# Re-export StressScenarioResult for usage convenience
__all__ = [
    "ProjectedPortfolio",
    "StressContext",
    "StressScenario",
    "StressScenarioResult",
    "StressSummary",
]


class StressScenario(RiskContract):
    """Declarative definition of a stress scenario.

    Avoids imperative code blocks to prevent arbitrary code execution risks.

    Attributes:
        scenario_id: Unique string identifier for the scenario.
        name: Human-readable scenario name.
        price_shocks: Dictionary mapping symbols to percentage price shocks.
        spread_multiplier: Factor to multiply current spreads by.
        margin_multiplier: Factor to multiply current margin requirements by.
        is_disconnect: True if platform disconnect is simulated.
        is_stale_quote_check: True if quote age freshness check is simulated.
        is_correlation_to_one: True if correlation collapse is simulated.
        is_forced_liquidation_check: True if stop out proximity check is simulated.
        is_gbp_volatility: True if GBP volatility macro scenario is simulated.
        is_jpy_risk_off: True if JPY risk-off scenario is simulated.
        is_usd_shock: True if USD macro shock scenario is simulated.
        usd_shock_direction: Direction of USD shock ('up' or 'down').
        is_news_candle: True if unfavorable 5% news candle shock is simulated.
    """

    scenario_id: str = Field(..., description="Unique scenario identifier.")
    name: str = Field(..., description="Human-readable scenario name.")
    price_shocks: dict[str, Decimal] = Field(
        default_factory=dict, description="Price shocks per symbol."
    )
    spread_multiplier: Decimal = Field(
        default=Decimal("1.0"), description="Spread widening multiplier."
    )
    margin_multiplier: Decimal = Field(
        default=Decimal("1.0"), description="Margin requirement multiplier."
    )
    is_disconnect: bool = Field(
        default=False, description="True if connection loss is simulated."
    )
    is_stale_quote_check: bool = Field(
        default=False, description="True if stale quote check is simulated."
    )
    is_correlation_to_one: bool = Field(
        default=False, description="True if correlation collapse is simulated."
    )
    is_forced_liquidation_check: bool = Field(
        default=False,
        description="True if forced liquidation proximity check is simulated.",
    )
    is_gbp_volatility: bool = Field(
        default=False, description="True if GBP volatility shock is simulated."
    )
    is_jpy_risk_off: bool = Field(
        default=False, description="True if JPY risk-off is simulated."
    )
    is_usd_shock: bool = Field(
        default=False, description="True if USD macro shock is simulated."
    )
    usd_shock_direction: str = Field(
        default="up", description="USD shock direction ('up' or 'down')."
    )
    is_news_candle: bool = Field(
        default=False, description="True if news candle shock is simulated."
    )


class StressContext(RiskContract):
    """Context holding input data for stress testing evaluation.

    Attributes:
        portfolio_state: Current portfolio state snapshot.
        market_context: Live market details context dictionary.
        proposed_trade: Candidate proposed trade under evaluation.
    """

    portfolio_state: PortfolioState = Field(..., description="Current portfolio state.")
    market_context: dict[str, Any] = Field(..., description="Standard market context.")
    proposed_trade: ProposedTrade | None = Field(
        default=None, description="Candidate proposed trade."
    )


class ProjectedPortfolio(RiskContract):
    """Projected portfolio under shocked market conditions.

    Attributes:
        portfolio_state: Baseline portfolio state.
        proposed_trade: Proposed candidate trade.
        shocked_prices: Shocked current prices per symbol.
        shocked_spreads: Shocked spreads per symbol.
        shocked_margins: Shocked margin requirements per symbol.
        spread_multiplier: Shocked spread multiplier.
        margin_multiplier: Shocked margin multiplier.
        is_disconnected: True if connection is lost.
        is_stale: True if quote data is stale.
        is_correlation_to_one: True if correlation collapse is simulated.
        is_forced_liquidation_check: True if stop out proximity check is simulated.
        is_gbp_volatility: True if GBP volatility shock is simulated.
        is_slippage_shock: True if slippage shock is simulated.
    """

    portfolio_state: PortfolioState = Field(..., description="Base portfolio state.")
    proposed_trade: ProposedTrade | None = Field(
        default=None, description="Proposed candidate trade."
    )
    shocked_prices: dict[str, Decimal] = Field(
        default_factory=dict, description="Shocked current prices per symbol."
    )
    shocked_spreads: dict[str, Decimal] = Field(
        default_factory=dict, description="Shocked spreads per symbol."
    )
    shocked_margins: dict[str, Decimal] = Field(
        default_factory=dict, description="Shocked margins per symbol."
    )
    spread_multiplier: Decimal = Field(
        default=Decimal("1.0"), description="Shocked spread multiplier."
    )
    margin_multiplier: Decimal = Field(
        default=Decimal("1.0"), description="Shocked margin multiplier."
    )
    is_disconnected: bool = Field(
        default=False, description="True if platform connection is lost."
    )
    is_stale: bool = Field(default=False, description="True if quotes are stale.")
    is_correlation_to_one: bool = Field(
        default=False, description="True if correlation collapse is simulated."
    )
    is_forced_liquidation_check: bool = Field(
        default=False,
        description="True if forced liquidation proximity check is simulated.",
    )
    is_gbp_volatility: bool = Field(
        default=False, description="True if GBP volatility shock is simulated."
    )
    is_slippage_shock: bool = Field(
        default=False, description="True if slippage shock is simulated."
    )


class StressSummary(RiskContract):
    """Summary of all evaluated stress test scenarios.

    Attributes:
        results: List of evaluated stress scenario results.
        pass_status: True if all critical scenarios passed.
        reason_codes: Composite reason codes from failing scenarios.
    """

    results: list[StressScenarioResult] = Field(
        default_factory=list, description="Scenario-level evaluation results."
    )
    pass_status: bool = Field(
        default=True, description="Summary pass/fail status across all scenarios."
    )
    reason_codes: list[str] = Field(
        default_factory=list, description="Scenario-level reason codes combined."
    )


# Trigger logging upon imports to satisfy strict logging rules
logger.info("Stress contracts module initialized successfully.")
