"""Cross-Check: Monte Carlo Retest Methods.

Description:
    Runs N Monte Carlo simulations perturbing historical price bars, spreads,
    slippages, starting bars, or strategy parameters, re-evaluating backtests
    and calculating empirical confidence bands.

Purpose:
    FEAT-RETESTER-CROSS-CHECKS: Full retest simulation cross-check.

Key Capabilities:
    - FR-cross-check-mc-retest: Execute perturbed market simulations and evaluate
      empirical confidence bands against acceptance criteria.

Python API Usage:
    from app.workspace.retester.cross_check_monte_carlo_retest import (
        CrossCheckMonteCarloRetestService,
        MCRetestConfig,
    )
    result = CrossCheckMonteCarloRetestService.run(strategy, bars, config)

CLI Usage:
    python -m app.cli retest cross-check-mc-retest --simulations 50
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from app.core.data.contracts import MarketBar
from app.core.host.logging import get_logger
from app.extend.monte_carlo.retest.catalog import MCRetestPerturbator
from app.workspace.algo_wizard.models import HSLStrategyDocument
from app.workspace.retester.cross_check_monte_carlo_manipulation import (
    STANDARD_CONFIDENCE_LEVELS,
    MCConfidenceBand,
    MCManipulationRunResult,
)
from app.workspace.retester.settings_cross_checks import CrossCheckCondition

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class MCRetestMethodSpec:
    """Specification of an active retest perturbation method."""

    method_id: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert method spec to dictionary."""
        return {"method_id": self.method_id, "params": dict(self.params)}


@dataclass(frozen=True, slots=True)
class MCRetestConfig:
    """Configuration for Monte Carlo Retest Methods cross-check."""

    enabled: bool = False
    simulations: int = 50
    seed: int = 42
    methods: tuple[MCRetestMethodSpec, ...] = ()
    confidence_level: int = 90
    acceptance_conditions: tuple[CrossCheckCondition, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "simulations": self.simulations,
            "seed": self.seed,
            "confidence_level": self.confidence_level,
            "acceptance_conditions": [c.to_dict() for c in self.acceptance_conditions],
        }


MIN_BARS_FOR_TREND = 2


class CrossCheckMonteCarloRetestService:
    """Service executing Monte Carlo Retest simulations."""

    @classmethod
    def run(
        cls,
        strategy: HSLStrategyDocument,
        bars: Sequence[MarketBar],
        config: MCRetestConfig,
        initial_capital: float = 10000.0,
    ) -> MCManipulationRunResult:
        """Execute N perturbed simulations and calculate confidence bands.

        Args:
            strategy: Strategy document candidate.
            bars: Input market bars.
            config: Retest simulation settings.
            initial_capital: Account starting balance.

        Returns:
            MCManipulationRunResult with empirical bands and criteria evaluation.
        """
        n_sims = max(1, config.simulations)
        sim_profits: list[float] = []
        sim_dds: list[float] = []
        sim_return_dds: list[float] = []
        sim_pfs: list[float] = []

        for sim_idx in range(n_sims):
            sim_seed = config.seed + sim_idx * 1009
            curr_strat = strategy
            curr_bars = tuple(bars)

            for m in config.methods:
                curr_strat, curr_bars = MCRetestPerturbator.perturb(
                    m.method_id,
                    curr_strat,
                    curr_bars,
                    m.params,
                    seed=sim_seed,
                )

            from app.core.enums import Timeframe
            from app.core.trading.backtest.contracts import BacktestSettings, RunSpec
            from app.core.trading.backtest.runner import BacktestRunner
            from app.core.trading.strategy.hsl.compiler import StrategyCompiler

            plan = StrategyCompiler().compile_to_runtime(curr_strat)
            actual = BacktestRunner().run(
                RunSpec(
                    plan,
                    curr_strat.strategy.universe.symbols[0],
                    Timeframe(curr_strat.strategy.timeframe.primary),
                    curr_bars,
                    BacktestSettings(initial_capital=initial_capital),
                )
            )
            net_profit = actual.metrics["net_profit"]
            dd_pct = actual.metrics["max_drawdown_pct"]
            rdd = net_profit / (initial_capital * dd_pct / 100.0) if dd_pct else 0.0
            pf = actual.metrics["profit_factor"]

            sim_profits.append(net_profit)
            sim_dds.append(dd_pct)
            sim_return_dds.append(rdd)
            sim_pfs.append(pf)

        sim_profits.sort()
        sim_dds.sort()
        sim_return_dds.sort()
        sim_pfs.sort()

        bands: list[MCConfidenceBand] = []
        for conf in STANDARD_CONFIDENCE_LEVELS:
            k_worst = max(
                0,
                min(n_sims - 1, math.floor((100.0 - conf) / 100.0 * (n_sims - 1))),
            )
            k_dd = max(0, min(n_sims - 1, math.floor(conf / 100.0 * (n_sims - 1))))

            bands.append(
                MCConfidenceBand(
                    confidence_pct=conf,
                    net_profit=round(sim_profits[k_worst], 2),
                    drawdown_pct=round(sim_dds[k_dd], 2),
                    return_dd_ratio=round(sim_return_dds[k_worst], 2),
                    profit_factor=round(sim_pfs[k_worst], 2),
                )
            )

        target_band = next(
            (b for b in bands if b.confidence_pct == config.confidence_level),
            bands[-1],
        )

        failure_reasons: list[str] = []
        band_metrics = {
            "NetProfit": target_band.net_profit,
            "DrawdownPct": target_band.drawdown_pct,
            "ReturnDDRatio": target_band.return_dd_ratio,
            "ProfitFactor": target_band.profit_factor,
        }

        for cond in config.acceptance_conditions:
            val = band_metrics.get(cond.metric, 0.0)
            if not cond.evaluate(val):
                failure_reasons.append(
                    f"MC Retest Condition '{cond.name}' failed at "
                    f"{config.confidence_level}%: {cond.metric}={val} "
                    f"{cond.operator} {cond.threshold}"
                )

        passed = len(failure_reasons) == 0
        logger.info(
            "FR-cross-check-mc-retest: ran %d retest sims, %d%% profit=%.2f, passed=%s",
            n_sims,
            config.confidence_level,
            target_band.net_profit,
            passed,
        )

        return MCManipulationRunResult(
            simulations=n_sims,
            bands=tuple(bands),
            passed=passed,
            failure_reasons=tuple(failure_reasons),
        )
