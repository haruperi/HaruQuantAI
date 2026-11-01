"""Cross-Check: Monte Carlo Trade Manipulation.

Description:
    Runs N Monte Carlo simulations applying trade-sequence manipulations
    (skips, reordering, execution degradation, block shuffles) without re-running
    the price bar engine, computing confidence bands (50%..99%) and evaluating
    acceptance criteria.

Purpose:
    FEAT-RETESTER-CROSS-CHECKS: Monte Carlo trade manipulation cross-check.

Key Capabilities:
    - FR-cross-check-mc-manipulation: Empirical confidence band calculation
      and criteria evaluation for trade manipulation simulations.

Python API Usage:
    from app.workspace.retester.cross_check_monte_carlo_manipulation import (
        CrossCheckMonteCarloManipulationService,
        MCManipulationConfig,
    )
    result = CrossCheckMonteCarloManipulationService.run(trades, 10000.0, config)

CLI Usage:
    python -m app.cli retest cross-check-mc-manipulation --simulations 200
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.monte_carlo.manipulation.randomly_skip_trades import SkipRandom
from app.extend.what_if.base import WhatIfRecord
from app.workspace.retester.settings_cross_checks import CrossCheckCondition

logger = get_logger(__name__)

STANDARD_CONFIDENCE_LEVELS: tuple[int, ...] = (
    50,
    60,
    70,
    75,
    80,
    85,
    90,
    95,
    97,
    98,
    99,
)


class SeededRng(SkipRandom):
    """Deterministic SkipRandom implementation powered by random.Random."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)  # noqa: S311

    @override
    def next_index(self, upper_exclusive: int) -> int:
        """Generate next random index bounded by upper_exclusive."""
        if upper_exclusive <= 1:
            return 0
        return self._rng.randrange(0, upper_exclusive)


@dataclass(frozen=True, slots=True)
class MCConfidenceBand:
    """Confidence metrics at a specific confidence level."""

    confidence_pct: int
    net_profit: float
    drawdown_pct: float
    return_dd_ratio: float
    profit_factor: float

    def to_dict(self) -> dict[str, Any]:
        """Convert band to dictionary."""
        return {
            "confidence_pct": self.confidence_pct,
            "net_profit": self.net_profit,
            "drawdown_pct": self.drawdown_pct,
            "return_dd_ratio": self.return_dd_ratio,
            "profit_factor": self.profit_factor,
        }


@dataclass(frozen=True, slots=True)
class MCManipulationConfig:
    """Configuration for Monte Carlo Trade Manipulation cross-check."""

    enabled: bool = False
    simulations: int = 200
    seed: int = 42
    methods: tuple[Any, ...] = ()
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


@dataclass(frozen=True, slots=True)
class MCManipulationRunResult:
    """Overall outcome of Monte Carlo Trade Manipulation simulation."""

    simulations: int
    bands: tuple[MCConfidenceBand, ...]
    passed: bool
    failure_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert run result to dictionary."""
        return {
            "simulations": self.simulations,
            "bands": [b.to_dict() for b in self.bands],
            "passed": self.passed,
            "failure_reasons": list(self.failure_reasons),
        }


class CrossCheckMonteCarloManipulationService:
    """Service executing Monte Carlo Trade Manipulation simulations."""

    @staticmethod
    def _evaluate_simulation(
        trades: Sequence[WhatIfRecord], initial_capital: float
    ) -> tuple[float, float, float, float]:
        """Compute simulation metrics: net profit, drawdown pct, return/DD, PF."""
        equity = initial_capital
        peak = equity
        max_dd = 0.0
        net_profit = 0.0
        gross_profit = 0.0
        gross_loss = 0.0

        for t in trades:
            if t.kind == "trade":
                p = t.net_profit
                net_profit += p
                if p > 0:
                    gross_profit += p
                else:
                    gross_loss += abs(p)

                equity += p
                peak = max(peak, equity)
                dd = (peak - equity) / peak if peak > 0 else 0.0
                max_dd = max(max_dd, dd)

        dd_pct = max_dd * 100.0
        return_dd = (net_profit / (initial_capital * max_dd)) if max_dd > 0 else 0.0
        pf = (gross_profit / gross_loss) if gross_loss > 0 else 999.0
        return net_profit, dd_pct, return_dd, pf

    @classmethod
    def run(
        cls,
        trades: Sequence[WhatIfRecord],
        initial_capital: float,
        config: MCManipulationConfig,
    ) -> MCManipulationRunResult:
        """Run N simulations and calculate empirical confidence bands.

        Args:
            trades: Candidate strategy trades.
            initial_capital: Starting equity.
            config: MC manipulation settings.

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
            sim_rng = SeededRng(sim_seed)
            current = list(trades)
            for m in config.methods:
                current = m.apply(current, rng=sim_rng)

            np_val, dd_val, rdd_val, pf_val = cls._evaluate_simulation(
                current, initial_capital
            )
            sim_profits.append(np_val)
            sim_dds.append(dd_val)
            sim_return_dds.append(rdd_val)
            sim_pfs.append(pf_val)

        # Sort ascending for percentile lookups
        sim_profits.sort()
        sim_dds.sort()
        sim_return_dds.sort()
        sim_pfs.sort()

        bands: list[MCConfidenceBand] = []
        for conf in STANDARD_CONFIDENCE_LEVELS:
            # Maximized metrics: worst-case is the (100 - conf)% percentile
            # e.g. 90% confidence level -> 10th percentile
            k_worst = max(
                0,
                min(n_sims - 1, math.floor((100.0 - conf) / 100.0 * (n_sims - 1))),
            )
            # Minimized metrics (drawdown): worst-case is the conf% percentile
            # e.g. 90% confidence level -> 90th percentile
            k_dd = max(0, min(n_sims - 1, math.floor(conf / 100.0 * (n_sims - 1))))

            bands.append(
                MCConfidenceBand(
                    confidence_pct=conf,
                    net_profit=round(sim_profits[k_worst], 2),
                    drawdown_pct=round(sim_dds[k_dd], 2),
                    return_dd_ratio=round(sim_return_dds[k_worst], 2),
                    profit_factor=round(min(sim_pfs[k_worst], 99.99), 2),
                )
            )

        # Evaluate acceptance conditions against specified confidence level band
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
                    f"MC Condition '{cond.name}' failed at "
                    f"{config.confidence_level}% confidence: {cond.metric}={val} "
                    f"{cond.operator} {cond.threshold}"
                )

        passed = len(failure_reasons) == 0
        logger.info(
            "FR-cross-check-mc-manipulation: completed %d simulations, "
            "%d%% profit=%.2f, passed=%s",
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
