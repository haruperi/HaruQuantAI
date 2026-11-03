"""Cross-Check: Retest with Higher Precision.

Description:
    Evaluates strategy performance using finer simulation precision (e.g. M1 data,
    tick data) and compares net profit and drawdown retention against the Main backtest.

Purpose:
    FEAT-RETESTER-CROSS-CHECKS: Higher precision backtest cross-check.

Key Capabilities:
    - FR-cross-check-higher-precision: Compare baseline vs higher-precision simulation
      retention and evaluate pass/fail criteria.

Python API Usage:
    from app.workspace.retester.cross_check_retest_with_higher_precision import (
        CrossCheckRetestWithHigherPrecisionService,
        HigherPrecisionConfig,
    )
    result = CrossCheckRetestWithHigherPrecisionService.run(strat, main_stats, config)

CLI Usage:
    python -m app.cli retest cross-check-higher-precision --precision M1Data
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.algo_wizard.models import HSLStrategyDocument
from app.workspace.retester.settings_cross_checks import CrossCheckCondition

logger = get_logger(__name__)

PrecisionType = Literal[
    "SelectedTimeframeOnly",
    "M1Data",
    "RealTickCustomSpread",
    "RealTickRealSpread",
]


@dataclass(frozen=True, slots=True)
class HigherPrecisionConfig:
    """Configuration for Higher Precision cross-check."""

    enabled: bool = False
    precision: PrecisionType = "M1Data"
    spread_pips: float | None = None
    min_profit_retention_pct: float = 70.0
    acceptance_conditions: tuple[CrossCheckCondition, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "precision": self.precision,
            "spread_pips": self.spread_pips,
            "min_profit_retention_pct": self.min_profit_retention_pct,
            "acceptance_conditions": [c.to_dict() for c in self.acceptance_conditions],
        }


@dataclass(frozen=True, slots=True)
class HigherPrecisionCheckResult:
    """Result of Higher Precision check evaluation."""

    precision: str
    main_net_profit: float
    hp_net_profit: float
    profit_retention_pct: float
    passed: bool
    failure_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "precision": self.precision,
            "main_net_profit": self.main_net_profit,
            "hp_net_profit": self.hp_net_profit,
            "profit_retention_pct": self.profit_retention_pct,
            "passed": self.passed,
            "failure_reasons": list(self.failure_reasons),
        }


class CrossCheckRetestWithHigherPrecisionService:
    """Service evaluating strategy robustness at higher simulation precision."""

    @classmethod
    def run(
        cls,
        strategy: HSLStrategyDocument,
        main_stats: Mapping[str, float],
        config: HigherPrecisionConfig,
        hp_stats: Mapping[str, float] | None = None,
    ) -> HigherPrecisionCheckResult:
        """Evaluate higher precision backtest metrics and profit retention.

        Args:
            strategy: Strategy document candidate.
            main_stats: Baseline simulation statistics (containing 'net_profit').
            config: Higher precision check settings.
            hp_stats: Higher precision simulation statistics (or None to simulate).

        Returns:
            HigherPrecisionCheckResult with retention percentage and pass/fail state.
        """
        if hp_stats is None:
            raise DomainError(
                code="HSL_RETEST_EVALUATOR_REQUIRED",
                message="This retest requires completed real evaluation results",
            )
        del strategy
        main_np = float(main_stats.get("net_profit", 0.0))

        required = ("net_profit", "drawdown_pct")
        if "net_profit" not in main_stats or any(
            key not in hp_stats for key in required
        ):
            raise DomainError(
                code="HSL_RETEST_EVIDENCE_INCOMPLETE",
                message="Both runs require complete observed metrics",
            )
        hp_np = float(hp_stats["net_profit"])
        hp_dd = float(hp_stats["drawdown_pct"])

        if not all(math.isfinite(value) for value in (main_np, hp_np, hp_dd)):
            raise DomainError(
                code="HSL_RETEST_EVIDENCE_INVALID",
                message="Retest metrics must be finite",
            )
        retention_pct = round((hp_np / main_np) * 100.0, 2) if main_np > 0 else 0.0

        failure_reasons: list[str] = []

        if retention_pct < config.min_profit_retention_pct:
            failure_reasons.append(
                f"Profit retention {retention_pct}% below required "
                f"{config.min_profit_retention_pct}%"
            )

        metrics = {
            "ProfitRetentionPct": retention_pct,
            "NetProfit": hp_np,
            "DrawdownPct": hp_dd,
        }

        for cond in config.acceptance_conditions:
            val = metrics.get(cond.metric, 0.0)
            if not cond.evaluate(val):
                failure_reasons.append(
                    f"Higher Precision Condition '{cond.name}' failed: "
                    f"{cond.metric}={val} {cond.operator} {cond.threshold}"
                )

        passed = len(failure_reasons) == 0
        logger.info(
            "FR-cross-check-higher-precision: precision=%s, main=%.2f, "
            "hp=%.2f, retention=%.2f%%, passed=%s",
            config.precision,
            main_np,
            hp_np,
            retention_pct,
            passed,
        )

        return HigherPrecisionCheckResult(
            precision=config.precision,
            main_net_profit=main_np,
            hp_net_profit=hp_np,
            profit_retention_pct=retention_pct,
            passed=passed,
            failure_reasons=tuple(failure_reasons),
        )
