"""Cross-Check: What-If Scenarios Simulation.

Description:
    Applies configured sequences of WhatIf trade filter scenarios to historical
    trades and verifies that resulting post-filter metrics satisfy defined
    acceptance conditions.

Purpose:
    FEAT-RETESTER-CROSS-CHECKS: What-If trade filtering cross-check.

Key Capabilities:
    - FR-cross-check-what-if: Sequentially filter trades through scenario rules
      and evaluate acceptance conditions on net profit and drawdown.

Python API Usage:
    from app.workspace.retester.cross_check_what_if import (
        CrossCheckWhatIfService,
        WhatIfCrossCheckConfig,
    )
    result = CrossCheckWhatIfService.run(
        records, initial_capital=10000.0, config=config
    )

CLI Usage:
    python -m app.cli retest cross-check-what-if --scenarios ExcludeShortTrades
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.extend.what_if.base import BaseWhatIf, WhatIfRecord
from app.workspace.retester.settings_cross_checks import CrossCheckCondition

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class WhatIfCrossCheckConfig:
    """Configuration for What-If scenario cross-check."""

    enabled: bool = False
    scenarios: tuple[BaseWhatIf, ...] = ()
    acceptance_conditions: tuple[CrossCheckCondition, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "scenarios": [s.name for s in self.scenarios],
            "acceptance_conditions": [c.to_dict() for c in self.acceptance_conditions],
        }


@dataclass(frozen=True, slots=True)
class WhatIfCrossCheckResult:
    """Result of What-If cross-check evaluation."""

    original_trade_count: int
    filtered_trade_count: int
    filtered_net_profit: float
    filtered_drawdown_pct: float
    passed: bool
    failure_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "original_trade_count": self.original_trade_count,
            "filtered_trade_count": self.filtered_trade_count,
            "filtered_net_profit": self.filtered_net_profit,
            "filtered_drawdown_pct": self.filtered_drawdown_pct,
            "passed": self.passed,
            "failure_reasons": list(self.failure_reasons),
        }


class CrossCheckWhatIfService:
    """Service executing What-If cross-check simulations."""

    @classmethod
    def run(
        cls,
        records: Sequence[WhatIfRecord],
        initial_capital: float,
        config: WhatIfCrossCheckConfig,
    ) -> WhatIfCrossCheckResult:
        """Execute What-If trade filtering pipeline and check acceptance conditions.

        Args:
            records: Immutable sequence of WhatIfRecord objects.
            initial_capital: Account starting balance.
            config: Cross-check configuration with scenarios and criteria.

        Returns:
            WhatIfCrossCheckResult with post-filter statistics and pass/fail state.
        """
        current_records: list[WhatIfRecord] = list(records)

        for scenario in config.scenarios:
            current_records = scenario.filter_trades(current_records)

        # Compute filtered equity curve and drawdown
        equity = initial_capital
        peak = equity
        max_dd = 0.0
        net_profit = 0.0

        for r in current_records:
            if r.kind == "trade":
                net_profit += r.net_profit
                equity += r.net_profit
                peak = max(peak, equity)
                dd = (peak - equity) / peak if peak > 0 else 0.0
                max_dd = max(max_dd, dd)

        dd_pct = round(max_dd * 100.0, 2)
        net_profit = round(net_profit, 2)

        # Evaluate acceptance conditions
        failure_reasons: list[str] = []
        metrics = {
            "NetProfit": net_profit,
            "DrawdownPct": dd_pct,
            "TradeCount": float(len(current_records)),
        }

        for cond in config.acceptance_conditions:
            val = metrics.get(cond.metric, 0.0)
            if not cond.evaluate(val):
                failure_reasons.append(
                    f"Condition '{cond.name}' failed: {cond.metric}={val} "
                    f"{cond.operator} {cond.threshold}"
                )

        passed = len(failure_reasons) == 0
        logger.info(
            "FR-cross-check-what-if: %d -> %d trades, profit=%.2f, dd=%.2f%%, "
            "passed=%s",
            len(records),
            len(current_records),
            net_profit,
            dd_pct,
            passed,
        )

        return WhatIfCrossCheckResult(
            original_trade_count=len(records),
            filtered_trade_count=len(current_records),
            filtered_net_profit=net_profit,
            filtered_drawdown_pct=dd_pct,
            passed=passed,
            failure_reasons=tuple(failure_reasons),
        )
