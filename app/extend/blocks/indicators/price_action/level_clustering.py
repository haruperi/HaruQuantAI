"""LevelClustering indicator.

- Identifies high-density price cluster zones and horizontal levels.
"""

from __future__ import annotations

import math
from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
MIN_CLUSTERING_LOOKBACK: int = 5
DEFAULT_CLUSTERING_LOOKBACK: int = 50
DEFAULT_TOLERANCE: float = 1.0
DEFAULT_HALF_LIFE: float = 20.0
CONFIRM_BARS: int = 2
CLUSTER_FOUND_THRESHOLD: float = 0.5


class LevelClustering(BaseIndicator):
    """Structural swing pivot level clustering block."""

    # Metadata: catalog identity, ports, and execution capabilities.
    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.price_action.level_clustering",
        version="1.0.0",
        name="LevelClustering",
        description=(
            "Identifies high-density price cluster zones and horizontal levels."
        ),
        category="price_action",
        tags=("price_action", "level-clustering"),
        execution_kind=ExecutionKind.EXPRESSION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "high", PortType.SERIES, required=True, description="High input series"
            ),
            InputPort(
                "low", PortType.SERIES, required=True, description="Low input series"
            ),
            InputPort(
                "close",
                PortType.SERIES,
                required=True,
                description="Close input series",
            ),
        ),
        outputs=(
            OutputPort(
                "cluster_price",
                PortType.SERIES,
                description="Cluster price output series",
            ),
            OutputPort(
                "cluster_weight",
                PortType.SERIES,
                description="Cluster weight output series",
            ),
            OutputPort(
                "cluster_found",
                PortType.SERIES,
                description="Cluster found output series",
            ),
        ),
        required_market_inputs=("high", "low", "close"),
        required_history_lookback=50,
        dependencies=(),
        is_generation_eligible=True,
        parameter_search_space={
            "lookback": {"type": "int", "min": 5, "max": 200, "default": 50},
            "tolerance": {
                "type": "float",
                "min": 0.0,
                "max": 4.0,
                "default": 1.0,
                "min_exclusive": True,
            },
        },
        is_deterministic=True,
        is_causal=True,
        supports_incremental=False,
    )

    # Parameters: validated user settings.
    lookback: int = Field(
        default=DEFAULT_CLUSTERING_LOOKBACK,
        ge=MIN_CLUSTERING_LOOKBACK,
        title="Lookback",
        description="Number of historical bars examined for patterns or levels",
    )

    tolerance: float = Field(
        default=DEFAULT_TOLERANCE,
        gt=0.0,
        title="Tolerance",
        description="Tolerance used by the indicator calculation",
    )

    # Parameter validation: only relationships and custom constraints.
    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.lookback < MIN_CLUSTERING_LOOKBACK:
            raise ValueError(
                f"lookback must be >= {MIN_CLUSTERING_LOOKBACK}, got {self.lookback}"
            )
        if self.tolerance <= 0.0:
            raise ValueError(f"tolerance must be > 0, got {self.tolerance}")
        return self

    # Required inputs: feeds needed by the selected settings.
    @override
    def required_inputs(self) -> tuple[str, ...]:
        """Return the market inputs needed by the selected settings."""
        return self.spec.required_market_inputs

    # Required history: retain the calculation's startup behavior.
    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return self.lookback

    # Calculation: log, check inputs, and return named aligned outputs.
    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        logger.debug(
            "FR-indicator-calculation: LevelClustering requested bars=%d", len(bars)
        )
        bars.require_inputs(self.required_inputs())
        high = bars.high
        low = bars.low
        close = bars.close
        lookback = self.lookback
        tolerance = self.tolerance
        logger.info(
            "LevelClustering.calculate called: lookback=%d, tol=%.2f",
            lookback,
            tolerance,
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        cl_price, cl_weight, cl_found = self._compute_clusters(
            (h_arr, l_arr, c_arr), lookback, tolerance
        )
        logger.info("LevelClustering completed: bars=%d", n)
        return {
            "cluster_price": IndicatorSeries(
                cl_price, name=f"ClusterPrice({lookback})"
            ),
            "cluster_weight": IndicatorSeries(
                cl_weight, name=f"ClusterWeight({lookback})"
            ),
            "cluster_found": IndicatorSeries(
                cl_found, name=f"ClusterFound({lookback})"
            ),
        }

    # Specialized methods: indicator-specific behavior only.
    @classmethod
    def _compute_clusters(
        cls,
        prices: tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]],
        lookback: int,
        tolerance: float,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        h_arr, l_arr, c_arr = prices
        n = len(c_arr)
        cl_price = np.copy(c_arr)
        cl_weight = np.zeros(n, dtype=np.float64)
        cl_found = np.zeros(n, dtype=np.float64)
        decay = math.log(2.0) / max(1.0, DEFAULT_HALF_LIFE)
        min_bars = 2 * CONFIRM_BARS + 1
        for i in range(min_bars - 1, n):
            start = max(0, i - lookback + 1)
            pivots = cls._extract_pivots(h_arr, l_arr, start, i)
            if not pivots:
                continue
            clusters = cls._group_clusters(pivots, tolerance)
            best_price, best_weight, found = cls._evaluate_best_cluster(
                clusters, c_arr[i], decay
            )
            if found:
                cl_price[i] = best_price
                cl_weight[i] = best_weight
                cl_found[i] = 1.0
        return (cl_price, cl_weight, cl_found)

    @classmethod
    def _extract_pivots(
        cls,
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        start: int,
        current: int,
    ) -> list[tuple[int, float]]:
        pivots: list[tuple[int, float]] = []
        p_start = max(start + CONFIRM_BARS, CONFIRM_BARS)
        p_end = current - CONFIRM_BARS + 1
        for idx in range(p_start, p_end):
            h_val = float(h_arr[idx])
            l_val = float(l_arr[idx])
            is_high = True
            is_low = True
            for offset in range(-CONFIRM_BARS, CONFIRM_BARS + 1):
                if offset == 0:
                    continue
                if h_arr[idx + offset] > h_val:
                    is_high = False
                if l_arr[idx + offset] < l_val:
                    is_low = False
            bars_ago = current - idx
            if is_high:
                pivots.append((bars_ago, h_val))
            if is_low:
                pivots.append((bars_ago, l_val))
        return pivots

    @classmethod
    def _group_clusters(
        cls, pivots: list[tuple[int, float]], tolerance: float
    ) -> list[list[tuple[int, float]]]:
        sorted_pivots = sorted(pivots, key=lambda x: x[1])
        clusters: list[list[tuple[int, float]]] = []
        cur_cluster: list[tuple[int, float]] = [sorted_pivots[0]]
        for p in sorted_pivots[1:]:
            if abs(p[1] - cur_cluster[0][1]) <= tolerance:
                cur_cluster.append(p)
            else:
                clusters.append(cur_cluster)
                cur_cluster = [p]
        if cur_cluster:
            clusters.append(cur_cluster)
        return clusters

    @classmethod
    def _evaluate_best_cluster(
        cls, clusters: list[list[tuple[int, float]]], current_close: float, decay: float
    ) -> tuple[float, float, bool]:
        best_price = current_close
        best_weight = 0.0
        best_dist = float("inf")
        found = False
        for cluster in clusters:
            weights = [math.exp(-decay * float(b)) for b, _ in cluster]
            tot_w = sum(weights)
            if tot_w <= 0.0:
                continue
            w_price = (
                sum((p * w for (_, p), w in zip(cluster, weights, strict=True))) / tot_w
            )
            dist = abs(current_close - w_price)
            if dist < best_dist:
                best_dist = dist
                best_price = w_price
                best_weight = tot_w
                found = True
        return (best_price, best_weight, found)

    @classmethod
    def has_cluster(cls, found_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if a valid cluster exists at shift."""
        logger.info("Evaluating LevelClustering.has_cluster: shift=%d", shift)
        return is_greater(
            found_series, CLUSTER_FOUND_THRESHOLD, shift1=shift, round_digits=8
        )

    @classmethod
    def is_near_cluster(
        cls,
        close: IndicatorSeries,
        cluster_price: IndicatorSeries,
        tolerance: float,
        shift: int = 0,
    ) -> bool:
        """True if close price is within tolerance of nearest cluster."""
        logger.info(
            "Evaluating LevelClustering.is_near_cluster: tol=%.2f, shift=%d",
            tolerance,
            shift,
        )
        c_val = close.get(shift)
        cl_val = cluster_price.get(shift)
        if np.isnan(c_val) or np.isnan(cl_val):
            return False
        return abs(c_val - cl_val) <= tolerance

    @classmethod
    def is_at_support(
        cls,
        close: IndicatorSeries,
        cluster_price: IndicatorSeries,
        tolerance: float,
        shift: int = 0,
    ) -> bool:
        """True if close is testing cluster from above (within tolerance)."""
        logger.info(
            "Evaluating LevelClustering.is_at_support: tol=%.2f, shift=%d",
            tolerance,
            shift,
        )
        c_val = close.get(shift)
        cl_val = cluster_price.get(shift)
        if np.isnan(c_val) or np.isnan(cl_val):
            return False
        return cl_val <= c_val <= cl_val + tolerance

    @classmethod
    def is_at_resistance(
        cls,
        close: IndicatorSeries,
        cluster_price: IndicatorSeries,
        tolerance: float,
        shift: int = 0,
    ) -> bool:
        """True if close is testing cluster from below (within tolerance)."""
        logger.info(
            "Evaluating LevelClustering.is_at_resistance: tol=%.2f, shift=%d",
            tolerance,
            shift,
        )
        c_val = close.get(shift)
        cl_val = cluster_price.get(shift)
        if np.isnan(c_val) or np.isnan(cl_val):
            return False
        return cl_val - tolerance <= c_val <= cl_val


# Public exports.
__all__ = ["LevelClustering"]
