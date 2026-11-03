"""Cross-Check: Retest on Additional Markets.

Description:
    Evaluates the strategy across multiple additional symbols, timeframes,
    and date ranges, storing sub-result keys (Additional_1, Additional_2, ...)
    and optionally generating a combined Portfolio result.

Purpose:
    FEAT-RETESTER-CROSS-CHECKS: Multi-market robustness cross-check.

Key Capabilities:
    - FR-cross-check-additional-markets: Evaluate strategy on additional market setups
      and generate sub-result projections.

Python API Usage:
    from app.workspace.retester.cross_check_retest_on_additional_markets import (
        AdditionalMarketSetup,
        AdditionalMarketsConfig,
        CrossCheckRetestOnAdditionalMarketsService,
    )
    result = CrossCheckRetestOnAdditionalMarketsService.run(strat, config)

CLI Usage:
    python -m app.cli retest cross-check-additional-markets --markets GBPUSD,H1
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.algo_wizard.models import HSLStrategyDocument
from app.workspace.retester.settings_cross_checks import CrossCheckCondition

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class AdditionalMarketSetup:
    """Configuration for an additional market retest run."""

    result_key: str
    symbol: str
    timeframe: str
    start_date: str | None = None
    end_date: str | None = None
    spread_pips: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert setup to dictionary."""
        return {
            "result_key": self.result_key,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "spread_pips": self.spread_pips,
        }


@dataclass(frozen=True, slots=True)
class AdditionalMarketsConfig:
    """Configuration for Additional Markets cross-check."""

    enabled: bool = False
    markets: tuple[AdditionalMarketSetup, ...] = ()
    compute_combined_portfolio: bool = True
    acceptance_conditions: tuple[CrossCheckCondition, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "markets": [m.to_dict() for m in self.markets],
            "compute_combined_portfolio": self.compute_combined_portfolio,
            "acceptance_conditions": [c.to_dict() for c in self.acceptance_conditions],
        }


@dataclass(frozen=True, slots=True)
class AdditionalMarketsCheckResult:
    """Result of Additional Markets cross-check evaluation."""

    market_results: dict[str, float]
    portfolio_net_profit: float
    passed: bool
    failure_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "market_results": dict(self.market_results),
            "portfolio_net_profit": self.portfolio_net_profit,
            "passed": self.passed,
            "failure_reasons": list(self.failure_reasons),
        }


class CrossCheckRetestOnAdditionalMarketsService:
    """Service evaluating strategy performance on additional symbols and markets."""

    @classmethod
    def run(
        cls,
        strategy: HSLStrategyDocument,
        config: AdditionalMarketsConfig,
        market_stats: Mapping[str, Mapping[str, float]] | None = None,
    ) -> AdditionalMarketsCheckResult:
        """Run retest on configured additional markets and compute combined portfolio.

        Args:
            strategy: Strategy document candidate.
            config: Additional markets configuration.
            market_stats: Optional precomputed stats per result key.

        Returns:
            AdditionalMarketsCheckResult with per-market results and pass/fail state.

        Raises:
            DomainError: If enabled=True and markets tuple is empty.
        """
        del strategy
        if config.enabled and len(config.markets) == 0:
            logger.error(
                "FR-cross-check-additional-markets: enabled but markets list is empty"
            )
            raise DomainError(
                code="RETESTER_ADDITIONAL_MARKETS_EMPTY",
                message="At least one additional market setup required when enabled",
            )

        if market_stats is None:
            raise DomainError(
                code="HSL_RETEST_EVALUATOR_REQUIRED",
                message="This retest requires completed real evaluation results",
            )
        results_map: dict[str, float] = {}
        total_profit = 0.0

        for setup in config.markets:
            if (
                setup.result_key not in market_stats
                or "net_profit" not in market_stats[setup.result_key]
            ):
                raise DomainError(
                    code="HSL_RETEST_EVIDENCE_INCOMPLETE",
                    message="Each requested market requires an observed net profit",
                )
            p = float(market_stats[setup.result_key]["net_profit"])
            if not math.isfinite(p):
                raise DomainError(
                    code="HSL_RETEST_EVIDENCE_INVALID",
                    message="Market result must be finite",
                )
            results_map[setup.result_key] = p
            total_profit += p

        portfolio_profit = (
            round(total_profit, 2) if config.compute_combined_portfolio else 0.0
        )
        if config.compute_combined_portfolio:
            results_map["Portfolio"] = portfolio_profit

        failure_reasons: list[str] = []
        metrics = {
            "PortfolioNetProfit": portfolio_profit,
            "MarketCount": float(len(config.markets)),
        }

        for cond in config.acceptance_conditions:
            val = metrics.get(cond.metric, 0.0)
            if not cond.evaluate(val):
                failure_reasons.append(
                    f"Additional Markets Condition '{cond.name}' failed: "
                    f"{cond.metric}={val} {cond.operator} {cond.threshold}"
                )

        passed = len(failure_reasons) == 0
        logger.info(
            "FR-cross-check-additional-markets: evaluated %d markets, "
            "portfolio=%.2f, passed=%s",
            len(config.markets),
            portfolio_profit,
            passed,
        )

        return AdditionalMarketsCheckResult(
            market_results=results_map,
            portfolio_net_profit=portfolio_profit,
            passed=passed,
            failure_reasons=tuple(failure_reasons),
        )
