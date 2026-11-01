"""Custom analysis snippet definitions and evaluators (CustomAnalysis cohort).

Description:
    Implements CorrelationFilterAnalyzer and OutlierTradeAnalyzer representing
    the 2 donor CustomAnalysis snippets for correlation pruning and outlier
    trade detection with adjusted net profit estimation.

Purpose:
    FEAT-EXTEND-CUSTOM-ANALYSIS: Custom analysis extension analyzers.

Key Capabilities:
    - FR-custom-analysis-correlation: Prune correlated strategy sets.
    - FR-custom-analysis-outliers: Detect outlier trades and adjust performance.

Python API Usage:
    from app.extend.custom_analysis.analyzers import CorrelationFilterAnalyzer
    retained = CorrelationFilterAnalyzer.evaluate(["S1", "S2"], matrix)

CLI Usage:
    python -m app.cli extend custom-analysis --analyze
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.extend.columns.base import TradeRecord

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class OutlierTradeReport:
    """Outlier trade analysis outcome and adjusted performance."""

    outlier_tickets: tuple[int, ...]
    mean_pl: float
    std_pl: float
    adjusted_net_profit: float

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary representation."""
        return {
            "outlier_tickets": list(self.outlier_tickets),
            "mean_pl": self.mean_pl,
            "std_pl": self.std_pl,
            "adjusted_net_profit": self.adjusted_net_profit,
        }


class CorrelationFilterAnalyzer:
    """Prunes correlated strategy sets based on pairwise correlation matrix."""

    @classmethod
    def evaluate(
        cls,
        strategy_ids: Sequence[str],
        correlation_matrix: Mapping[str, Mapping[str, float]],
        *,
        max_correlation: float = 0.5,
    ) -> tuple[str, ...]:
        """Return retained strategy IDs with correlation below threshold."""
        logger.info(
            "FR-custom-analysis-correlation: pruning %d strategies with max_corr=%.2f",
            len(strategy_ids),
            max_correlation,
        )
        retained: list[str] = []

        for sid in strategy_ids:
            is_correlated = False
            for r in retained:
                corr = correlation_matrix.get(sid, {}).get(r, 0.0)
                if abs(corr) >= max_correlation:
                    is_correlated = True
                    break
            if not is_correlated:
                retained.append(sid)

        return tuple(retained)


class OutlierTradeAnalyzer:
    """Identifies outlier trades exceeding standard deviation thresholds."""

    @classmethod
    def evaluate(
        cls,
        trades: Sequence[TradeRecord],
        *,
        std_multiplier: float = 3.0,
    ) -> OutlierTradeReport:
        """Detect trades exceeding std_multiplier deviations from mean."""
        logger.info(
            "FR-custom-analysis-outliers: analyzing %d trades with multiplier=%.1f",
            len(trades),
            std_multiplier,
        )
        if not trades:
            return OutlierTradeReport(
                outlier_tickets=(),
                mean_pl=0.0,
                std_pl=0.0,
                adjusted_net_profit=0.0,
            )

        pls = [t.profit_loss for t in trades]
        n = len(pls)
        mean_pl = sum(pls) / n
        variance = sum((p - mean_pl) ** 2 for p in pls) / n
        std_pl = math.sqrt(variance)

        outliers: list[int] = []
        normal_pls: list[float] = []

        threshold = std_multiplier * std_pl

        for t in trades:
            diff = abs(t.profit_loss - mean_pl)
            if std_pl > 0.0 and diff > threshold:
                outliers.append(t.ticket)
            else:
                normal_pls.append(t.profit_loss)

        adjusted_profit = round(sum(normal_pls), 2)

        return OutlierTradeReport(
            outlier_tickets=tuple(outliers),
            mean_pl=round(mean_pl, 2),
            std_pl=round(std_pl, 2),
            adjusted_net_profit=adjusted_profit,
        )
