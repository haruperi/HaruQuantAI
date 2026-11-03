"""Cross-Check: Walk-Forward Optimization (WFO).

Description:
    Splits the historical bar timeline into rolling or anchored In-Sample (IS)
    optimization windows and Out-of-Sample (OOS) forward test windows, stitching
    forward results and evaluating Walk-Forward efficiency and profitable runs ratio.

Purpose:
    FEAT-RETESTER-CROSS-CHECKS: Walk-Forward Optimization robustness check.

Key Capabilities:
    - FR-cross-check-wfo: Partition history into IS/OOS segments, stitch forward trades,
      and compute Walk-Forward efficiency ratio.

Python API Usage:
    from app.workspace.retester.cross_check_walk_forward_optimization import (
        CrossCheckWalkForwardOptimizationService,
        WFOptimizationConfig,
    )
    result = CrossCheckWalkForwardOptimizationService.run(strat, bars, config)

CLI Usage:
    python -m app.cli retest cross-check-wfo --runs 10 --oos-pct 30
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.core.data.contracts import MarketBar
from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.strategy.hsl.models import HSLStrategyDocument
from app.workspace.retester.settings_cross_checks import CrossCheckCondition

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class WFOptimizationConfig:
    """Configuration for Walk-Forward Optimization cross-check."""

    enabled: bool = False
    runs_count: int = 10
    oos_pct: int = 30
    anchored: bool = False
    fitness_metric: str = "NetProfit"
    acceptance_conditions: tuple[CrossCheckCondition, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "runs_count": self.runs_count,
            "oos_pct": self.oos_pct,
            "anchored": self.anchored,
            "fitness_metric": self.fitness_metric,
            "acceptance_conditions": [c.to_dict() for c in self.acceptance_conditions],
        }


@dataclass(frozen=True, slots=True)
class WFWindowResult:
    """Result of an individual Walk-Forward IS/OOS window."""

    window_index: int
    is_start_ms: int
    is_end_ms: int
    oos_start_ms: int
    oos_end_ms: int
    best_params: dict[str, float | int]
    is_net_profit: float
    oos_net_profit: float
    oos_trades: int

    def to_dict(self) -> dict[str, Any]:
        """Convert window result to dictionary."""
        return {
            "window_index": self.window_index,
            "is_start_ms": self.is_start_ms,
            "is_end_ms": self.is_end_ms,
            "oos_start_ms": self.oos_start_ms,
            "oos_end_ms": self.oos_end_ms,
            "best_params": dict(self.best_params),
            "is_net_profit": self.is_net_profit,
            "oos_net_profit": self.oos_net_profit,
            "oos_trades": self.oos_trades,
        }


@dataclass(frozen=True, slots=True)
class WFOptimizationCheckResult:
    """Aggregated result of Walk-Forward Optimization."""

    windows: tuple[WFWindowResult, ...]
    stitched_oos_net_profit: float
    wf_efficiency_pct: float
    profitable_runs_pct: float
    passed: bool
    failure_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert check result to dictionary."""
        return {
            "windows": [w.to_dict() for w in self.windows],
            "stitched_oos_net_profit": self.stitched_oos_net_profit,
            "wf_efficiency_pct": self.wf_efficiency_pct,
            "profitable_runs_pct": self.profitable_runs_pct,
            "passed": self.passed,
            "failure_reasons": list(self.failure_reasons),
        }


class CrossCheckWalkForwardOptimizationService:
    """Service executing Walk-Forward Optimization partitioning and evaluation."""

    @classmethod
    def run(
        cls,
        strategy: HSLStrategyDocument,
        bars: Sequence[MarketBar],
        config: WFOptimizationConfig,
        custom_window_returns: Sequence[float] | None = None,
    ) -> WFOptimizationCheckResult:
        """Run Walk-Forward Optimization across time windows.

        Args:
            strategy: Strategy document candidate.
            bars: Input market bars.
            config: Walk-forward optimization settings.
            custom_window_returns: Optional pre-defined OOS profits for test fixtures.

        Returns:
            WFOptimizationCheckResult with stitched metrics and condition verification.
        """
        del strategy, bars, config, custom_window_returns
        logger.error(
            "FR-cross-check-evidence: complete evaluation evidence is required"
        )
        raise DomainError(
            code="HSL_RETEST_EVALUATOR_REQUIRED",
            message="Complete run metrics are required; adapter is not qualified",
        )
