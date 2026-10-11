"""Structural Level Clustering Indicator Block.

Description:
    Identifies confirmed swing pivot levels over a trailing lookback window,
    clusters them by price proximity within a configurable tolerance, and
    computes the nearest cluster price weighted by exponential recency decay:
    - Weight: w = exp(-lambda * bars_ago) where lambda = ln(2) / half_life.
    - Cluster Price: Sum(price * w) / Sum(w).
    - Evaluates whether the current price is testing key support or resistance
      clusters.

Purpose:
    FEAT-BLOCKS-INDICATOR-LEVEL-CLUSTERING

Key Capabilities:
    - FR-BLOCKS-LEVEL-CLUSTERING-CALCULATE: Identifies confirmed swing extrema,
      performs greedy 1D price clustering, and applies recency weighting.
    - FR-BLOCKS-LEVEL-CLUSTERING-CONDITIONS: Evaluates cluster existence,
      proximity, and support/resistance tests.

Python API Usage:
    ```python
    from app.blocks.indicators.price_action.level_clustering import (
        LevelClustering,
    )

    clusters = LevelClustering.calculate(high, low, close, lookback=50, tolerance=1.0)
    cluster_price = clusters["cluster_price"]
    cluster_weight = clusters["cluster_weight"]

    # Condition checks
    is_supp = LevelClustering.is_at_support(close, cluster_price, tolerance=1.0)
    is_res = LevelClustering.is_at_resistance(close, cluster_price, tolerance=1.0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

import math
from typing import Any, override

import numpy as np

from app.blocks.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)

MIN_CLUSTERING_LOOKBACK: int = 5
DEFAULT_CLUSTERING_LOOKBACK: int = 50
DEFAULT_TOLERANCE: float = 1.0
DEFAULT_HALF_LIFE: float = 20.0
CONFIRM_BARS: int = 2
CLUSTER_FOUND_THRESHOLD: float = 0.5


class LevelClustering(BaseIndicator):
    """Structural swing pivot level clustering block."""

    @classmethod
    @override
    def calculate(
        cls,
        high: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        low: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        close: list[float] | np.ndarray[Any, Any] | IndicatorSeries,
        lookback: int = DEFAULT_CLUSTERING_LOOKBACK,
        tolerance: float = DEFAULT_TOLERANCE,
    ) -> dict[str, IndicatorSeries]:
        """Compute nearest recency-weighted pivot cluster levels.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            lookback: Trailing window size for pivot identification.
            tolerance: Price grouping tolerance distance for merging pivots.

        Returns:
            Dictionary containing 'cluster_price', 'cluster_weight', and
            'cluster_found' IndicatorSeries.
        """
        logger.info(
            "LevelClustering.calculate called: lookback=%d, tol=%.2f",
            lookback,
            tolerance,
        )
        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)

        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n:
            raise ValueError("Arrays cannot be empty and lengths must match")
        if lookback < MIN_CLUSTERING_LOOKBACK:
            raise ValueError(
                f"lookback must be >= {MIN_CLUSTERING_LOOKBACK}, got {lookback}"
            )
        if tolerance <= 0.0:
            raise ValueError(f"tolerance must be > 0, got {tolerance}")

        cl_price, cl_weight, cl_found = cls._compute_clusters(
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

    @classmethod
    def _compute_clusters(
        cls,
        prices: tuple[
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
            np.ndarray[Any, Any],
        ],
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

        return cl_price, cl_weight, cl_found

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
        cls,
        pivots: list[tuple[int, float]],
        tolerance: float,
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
        cls,
        clusters: list[list[tuple[int, float]]],
        current_close: float,
        decay: float,
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
                sum(p * w for (_, p), w in zip(cluster, weights, strict=True)) / tot_w
            )
            dist = abs(current_close - w_price)
            if dist < best_dist:
                best_dist = dist
                best_price = w_price
                best_weight = tot_w
                found = True

        return best_price, best_weight, found

    @classmethod
    def has_cluster(cls, found_series: IndicatorSeries, shift: int = 0) -> bool:
        """True if a valid cluster exists at shift."""
        logger.info("Evaluating LevelClustering.has_cluster: shift=%d", shift)
        val = found_series.get(shift)
        return not np.isnan(val) and val > CLUSTER_FOUND_THRESHOLD

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
        return cl_val <= c_val <= (cl_val + tolerance)

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
        return (cl_val - tolerance) <= c_val <= cl_val
