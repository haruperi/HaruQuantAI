"""System Parameter Permutation (SPP) results view and projection service.

Description:
    Implements ResultsSysParamPermutationService projecting original vs. median
    vs. confidence-percentile metrics across permuted parameter runs.

Purpose:
    FEAT-RESULTS-SYS-PARAM-PERMUTATION: System parameter permutation projection.

Key Capabilities:
    - FR-spp-summary-projection: Compute distribution statistics.
    - FR-spp-runs-table: Paginated table of individual parameter permutation runs.

Python API Usage:
    from app.workspace.optimizer.results_sys_param_permutation import (
        ResultsSysParamPermutationService,
    )
    service = ResultsSysParamPermutationService()
    resp = service.get_projection("Strat_01")

CLI Usage:
    python -m app.cli optimizer spp-summary --strategy-id Strat_01
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.responses import StandardResponse
from app.workspace.optimizer.common import wrap_response
from app.workspace.optimizer.results_optimization_profile import OptimizationRunRow

logger = get_logger(__name__)


def _calc_percentile(sorted_values: Sequence[float], p: float) -> float:
    """Calculate percentile p (0-100) using linear interpolation."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]

    k = (len(sorted_values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    d0 = sorted_values[int(f)] * (c - k)
    d1 = sorted_values[int(c)] * (k - f)
    return d0 + d1


@dataclass(frozen=True, slots=True)
class SPPMetricSummaryRow:
    """Summary distribution statistics for single metric across permutation runs."""

    metric_id: str
    label: str
    original_value: float
    median_value: float
    mean_value: float
    std_dev: float
    percentile_5: float
    percentile_95: float

    def to_dict(self) -> dict[str, Any]:
        """Convert metric summary row to dictionary."""
        return {
            "metric_id": self.metric_id,
            "label": self.label,
            "original_value": self.original_value,
            "median_value": self.median_value,
            "mean_value": self.mean_value,
            "std_dev": self.std_dev,
            "percentile_5": self.percentile_5,
            "percentile_95": self.percentile_95,
        }


@dataclass(frozen=True, slots=True)
class SPPResultsProjection:
    """Complete SPP distribution summary and histogram projection."""

    strategy_id: str
    total_permutations: int
    profitable_runs_pct: float
    summary_rows: tuple[SPPMetricSummaryRow, ...]
    histogram_bins: tuple[tuple[float, int], ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert projection to dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "total_permutations": self.total_permutations,
            "profitable_runs_pct": self.profitable_runs_pct,
            "summary_rows": [r.to_dict() for r in self.summary_rows],
            "histogram_bins": [list(b) for b in self.histogram_bins],
        }


class ResultsSysParamPermutationService:
    """Service generating SPP statistical summaries and runs tables."""

    def __init__(self) -> None:
        """Initialize service with in-memory store for permutation runs."""
        self._runs_by_strategy: dict[str, list[OptimizationRunRow]] = {}
        self._original_metrics: dict[str, dict[str, float]] = {}

    def set_runs(
        self,
        strategy_id: str,
        runs: list[OptimizationRunRow],
        original_metrics: dict[str, float] | None = None,
    ) -> None:
        """Register permutation runs for strategy."""
        self._runs_by_strategy[strategy_id] = runs
        self._original_metrics[strategy_id] = original_metrics or {}

    def get_projection(
        self, strategy_id: str
    ) -> StandardResponse[SPPResultsProjection]:
        """Compute statistical summary across all permutation runs for strategy.

        Args:
            strategy_id: Strategy identifier.

        Returns:
            StandardResponse containing SPPResultsProjection.
        """
        runs = self._runs_by_strategy.get(strategy_id, [])
        if not runs:
            empty_proj = SPPResultsProjection(
                strategy_id=strategy_id,
                total_permutations=0,
                profitable_runs_pct=0.0,
                summary_rows=(),
                histogram_bins=(),
            )
            return wrap_response(
                request_id=f"req_{strategy_id}_spp_proj",
                data=empty_proj,
                json_payload=empty_proj.to_dict(),
            )

        total_perms = len(runs)
        orig_metrics = self._original_metrics.get(strategy_id, {})

        # Collect metrics across all runs
        metric_values: dict[str, list[float]] = {}
        for r in runs:
            for m_key, m_val in r.metrics.items():
                if m_key not in metric_values:
                    metric_values[m_key] = []
                metric_values[m_key].append(float(m_val))

        summary_rows: list[SPPMetricSummaryRow] = []
        for m_key, vals in metric_values.items():
            sorted_vals = sorted(vals)
            med = float(statistics.median(sorted_vals))
            avg = float(statistics.mean(sorted_vals))
            stdev = (
                float(statistics.stdev(sorted_vals)) if len(sorted_vals) > 1 else 0.0
            )
            p5 = _calc_percentile(sorted_vals, 5.0)
            p95 = _calc_percentile(sorted_vals, 95.0)
            orig = orig_metrics.get(m_key, med)

            summary_rows.append(
                SPPMetricSummaryRow(
                    metric_id=m_key,
                    label=m_key,
                    original_value=round(orig, 4),
                    median_value=round(med, 4),
                    mean_value=round(avg, 4),
                    std_dev=round(stdev, 4),
                    percentile_5=round(p5, 4),
                    percentile_95=round(p95, 4),
                )
            )

        # NetProfit profitable runs percentage & histogram
        np_vals = metric_values.get("NetProfit", [0.0])
        profitable_count = sum(1 for v in np_vals if v > 0.0)
        profitable_pct = round((profitable_count / total_perms) * 100.0, 2)

        # Construct 5 simple histogram bins for NetProfit
        min_v = min(np_vals)
        max_v = max(np_vals)
        if min_v == max_v:
            hist_bins: tuple[tuple[float, int], ...] = ((min_v, total_perms),)
        else:
            num_bins = 5
            last_bin_idx = num_bins - 1
            bin_width = (max_v - min_v) / float(num_bins)
            bins: list[tuple[float, int]] = []
            for i in range(num_bins):
                b_center = round(min_v + (i + 0.5) * bin_width, 2)
                b_low = min_v + i * bin_width
                b_high = min_v + (i + 1) * bin_width
                if i == last_bin_idx:
                    c = sum(1 for v in np_vals if b_low <= v <= b_high)
                else:
                    c = sum(1 for v in np_vals if b_low <= v < b_high)
                bins.append((b_center, c))
            hist_bins = tuple(bins)

        projection = SPPResultsProjection(
            strategy_id=strategy_id,
            total_permutations=total_perms,
            profitable_runs_pct=profitable_pct,
            summary_rows=tuple(summary_rows),
            histogram_bins=hist_bins,
        )
        logger.info(
            "Computed SPP projection for %s: %d perms, %f%% profitable",
            strategy_id,
            total_perms,
            profitable_pct,
        )
        return wrap_response(
            request_id=f"req_{strategy_id}_spp_proj",
            data=projection,
            json_payload=projection.to_dict(),
        )

    def get_table(
        self, strategy_id: str, *, offset: int = 0, limit: int = 200
    ) -> StandardResponse[tuple[OptimizationRunRow, ...]]:
        """Retrieve paginated slice of permutation runs.

        Args:
            strategy_id: Strategy identifier.
            offset: Starting index offset.
            limit: Maximum items to return.

        Returns:
            StandardResponse containing tuple of OptimizationRunRow.
        """
        all_runs = self._runs_by_strategy.get(strategy_id, [])
        sliced = all_runs[offset : offset + limit]
        return wrap_response(
            request_id=f"req_{strategy_id}_spp_table",
            data=tuple(sliced),
            json_payload=[r.to_dict() for r in sliced],
        )
