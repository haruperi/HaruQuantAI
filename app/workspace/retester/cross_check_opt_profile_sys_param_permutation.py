"""Cross-Check: Optimization Profile & System Parameter Permutation (SPP).

Description:
    Evaluates parameter neighborhood stability by perturbing strategy parameters
    across increments (+/- pct_change), computing the percentage of profitable
    combinations and median returns.

Purpose:
    FEAT-RETESTER-CROSS-CHECKS: System parameter permutation stability cross-check.

Key Capabilities:
    - FR-cross-check-spp: Permute parameters across neighborhood grid.

Python API Usage:
    from app.workspace.retester.cross_check_opt_profile_sys_param_permutation import (
        CrossCheckOptProfileSPPService,
        SPPConfig,
    )
    result = CrossCheckOptProfileSPPService.run(strat, bars, config)

CLI Usage:
    python -m app.cli retest cross-check-spp --max-tests 100 --pct-change 20.0
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.core.data.contracts import MarketBar
from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.algo_wizard.models import HSLStrategyDocument

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SPPConfig:
    """Configuration for System Parameter Permutation (SPP) cross-check."""

    enabled: bool = False
    max_tests: int = 100
    pct_change: float = 20.0
    steps: int = 5
    min_profitable_runs_pct: float = 70.0
    seed: int = 42

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "max_tests": self.max_tests,
            "pct_change": self.pct_change,
            "steps": self.steps,
            "min_profitable_runs_pct": self.min_profitable_runs_pct,
            "seed": self.seed,
        }


@dataclass(frozen=True, slots=True)
class SPPResult:
    """Result of SPP evaluation."""

    total_runs: int
    profitable_runs_pct: float
    median_net_profit: float
    median_return_dd: float
    avg_parameter_stability: float
    passed: bool
    failure_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "total_runs": self.total_runs,
            "profitable_runs_pct": self.profitable_runs_pct,
            "median_net_profit": self.median_net_profit,
            "median_return_dd": self.median_return_dd,
            "avg_parameter_stability": self.avg_parameter_stability,
            "passed": self.passed,
            "failure_reasons": list(self.failure_reasons),
        }


class CrossCheckOptProfileSPPService:
    """Service evaluating System Parameter Permutation stability."""

    @classmethod
    def run(
        cls,
        strategy: HSLStrategyDocument,
        bars: Sequence[MarketBar],
        config: SPPConfig,
        custom_runs: Sequence[float] | None = None,
    ) -> SPPResult:
        """Run parameter permutations and compute stability metrics.

        Args:
            strategy: Strategy document candidate.
            bars: Input market bars.
            config: SPP cross-check configuration.
            custom_runs: Optional pre-defined profits for test fixtures.

        Returns:
            SPPResult with profitable ratio, median profit, and pass/fail state.
        """
        del strategy, bars, config, custom_runs
        logger.error(
            "FR-cross-check-evidence: complete evaluation evidence is required"
        )
        raise DomainError(
            code="HSL_RETEST_EVALUATOR_REQUIRED",
            message="Complete run metrics are required; adapter is not qualified",
        )
