"""Ichimoku Kinko Hyo Indicator Block.

Description:
    Implements the complete Ichimoku Kinko Hyo indicator system, comprising
    Tenkan-sen (Conversion Line), Kijun-sen (Base Line), Senkou Span A (Leading
    Span A), Senkou Span B (Leading Span B), and Chikou Span (Lagging Span).
    Provides condition evaluators for Tenkan/Kijun crosses and Kumo breakouts.

Purpose:
    FEAT-BLOCKS-INDICATOR-ICHIMOKU

Key Capabilities:
    - FR-BLOCKS-ICHIMOKU-CALCULATE: Computes all 5 Ichimoku lines and Kumo cloud.
    - FR-BLOCKS-ICHIMOKU-CONDITIONS: Evaluates TK crosses and Kumo breakouts.

Python API Usage:
    ```python
    from app.blocks.indicators.ichimoku import Ichimoku

    ichi = Ichimoku.calculate(high, low, close, tenkan=9, kijun=26, senkou=52)
    ts = ichi["tenkan_sen"]
    ks = ichi["kijun_sen"]
    sa = ichi["senkou_span_a"]
    sb = ichi["senkou_span_b"]

    # Condition checks
    tk_bull = Ichimoku.tenkan_kijun_cross_bullish(ts, ks, shift=0)
    kumo_break = Ichimoku.kumo_breakout_bullish(close, sa, sb, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.blocks.base import BaseIndicator, IndicatorSeries
from app.host.logging import get_logger

logger = get_logger(__name__)

DEFAULT_TENKAN: int = 9
DEFAULT_KIJUN: int = 26
DEFAULT_SENKOU: int = 52


class Ichimoku(BaseIndicator):
    """Ichimoku Kinko Hyo indicator block."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        tenkan: int = DEFAULT_TENKAN,
        kijun: int = DEFAULT_KIJUN,
        senkou: int = DEFAULT_SENKOU,
    ) -> dict[str, IndicatorSeries]:
        """Compute the 5 Ichimoku lines and Kumo cloud bounds.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            tenkan: Conversion line lookback (default 9).
            kijun: Base line lookback (default 26).
            senkou: Leading Span B lookback (default 52).

        Returns:
            Dictionary containing:
                - 'tenkan_sen': Conversion line.
                - 'kijun_sen': Base line.
                - 'senkou_span_a': Leading Span A.
                - 'senkou_span_b': Leading Span B.
                - 'chikou_span': Lagging Span.

        Raises:
            ValueError: If periods are < 1 or array lengths mismatch.
        """
        logger.info(
            "Ichimoku calculation initiated: tenkan=%d, kijun=%d, senkou=%d",
            tenkan,
            kijun,
            senkou,
            extra={"tenkan": tenkan, "kijun": kijun, "senkou": senkou},
        )
        if tenkan < 1 or kijun < 1 or senkou < 1:
            raise ValueError("All lookback periods must be >= 1")

        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)

        n = len(c_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        if not (len(h_arr) == len(l_arr) == n):
            raise ValueError("High, Low, and Close array lengths must match")

        ts_vals, ks_vals = cls._calc_tenkan_kijun(h_arr, l_arr, tenkan, kijun)
        sum_a = (ts_vals + ks_vals) / 2.0
        sa_vals, sb_vals = cls._calc_senkou_spans(h_arr, l_arr, sum_a, kijun, senkou)
        cs_vals = cls._calc_chikou_span(c_arr, kijun)

        logger.info(
            "Ichimoku calculation complete: bars=%d",
            n,
            extra={"bars": n},
        )
        return {
            "tenkan_sen": IndicatorSeries(ts_vals, name=f"TenkanSen({tenkan})"),
            "kijun_sen": IndicatorSeries(ks_vals, name=f"KijunSen({kijun})"),
            "senkou_span_a": IndicatorSeries(sa_vals, name=f"SenkouSpanA({kijun})"),
            "senkou_span_b": IndicatorSeries(sb_vals, name=f"SenkouSpanB({senkou})"),
            "chikou_span": IndicatorSeries(cs_vals, name=f"ChikouSpan({kijun})"),
        }

    @staticmethod
    def _calc_tenkan_kijun(
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        tenkan: int,
        kijun: int,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        n = len(h_arr)
        ts = np.full(n, np.nan, dtype=np.float64)
        ks = np.full(n, np.nan, dtype=np.float64)

        for i in range(n):
            if i >= tenkan - 1:
                h_win = h_arr[i - tenkan + 1 : i + 1]
                l_win = l_arr[i - tenkan + 1 : i + 1]
                ts[i] = (np.max(h_win) + np.min(l_win)) / 2.0
            else:
                ts[i] = (h_arr[i] + l_arr[i]) / 2.0

            if i >= kijun - 1:
                h_win2 = h_arr[i - kijun + 1 : i + 1]
                l_win2 = l_arr[i - kijun + 1 : i + 1]
                ks[i] = (np.max(h_win2) + np.min(l_win2)) / 2.0
            else:
                ks[i] = (h_arr[i] + l_arr[i]) / 2.0

        return ts, ks

    @staticmethod
    def _calc_senkou_spans(
        h_arr: np.ndarray[Any, Any],
        l_arr: np.ndarray[Any, Any],
        sum_a: np.ndarray[Any, Any],
        kijun: int,
        senkou: int,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        n = len(h_arr)
        sa = np.full(n, np.nan, dtype=np.float64)
        sb = np.full(n, np.nan, dtype=np.float64)
        sum_b = np.full(n, np.nan, dtype=np.float64)

        for i in range(n):
            if i >= senkou - 1:
                h_win = h_arr[i - senkou + 1 : i + 1]
                l_win = l_arr[i - senkou + 1 : i + 1]
                sum_b[i] = (np.max(h_win) + np.min(l_win)) / 2.0
            else:
                sum_b[i] = (h_arr[i] + l_arr[i]) / 2.0

        # Current bar value is projected from kijun bars ago
        for i in range(kijun, n):
            sa[i] = sum_a[i - kijun]
            sb[i] = sum_b[i - kijun]

        return sa, sb

    @staticmethod
    def _calc_chikou_span(
        c_arr: np.ndarray[Any, Any],
        kijun: int,
    ) -> np.ndarray[Any, Any]:
        n = len(c_arr)
        cs = np.full(n, np.nan, dtype=np.float64)
        for i in range(n - kijun):
            cs[i] = c_arr[i + kijun]
        return cs

    @staticmethod
    def tenkan_kijun_cross_bullish(
        tenkan_sen: IndicatorSeries | np.ndarray[Any, Any],
        kijun_sen: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Tenkan-sen crossed above Kijun-sen."""
        logger.info("Evaluating Ichimoku tenkan_kijun_cross_bullish at shift=%d", shift)
        ts = BaseIndicator.to_numpy(tenkan_sen)
        ks = BaseIndicator.to_numpy(kijun_sen)
        curr = len(ts) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(ts) or curr >= len(ks):
            return False
        if np.isnan(ts[curr]) or np.isnan(ks[curr]) or np.isnan(ts[prev]):
            return False
        return bool(ts[prev] <= ks[prev] and ts[curr] > ks[curr])

    @staticmethod
    def tenkan_kijun_cross_bearish(
        tenkan_sen: IndicatorSeries | np.ndarray[Any, Any],
        kijun_sen: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Tenkan-sen crossed below Kijun-sen."""
        logger.info("Evaluating Ichimoku tenkan_kijun_cross_bearish at shift=%d", shift)
        ts = BaseIndicator.to_numpy(tenkan_sen)
        ks = BaseIndicator.to_numpy(kijun_sen)
        curr = len(ts) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(ts) or curr >= len(ks):
            return False
        if np.isnan(ts[curr]) or np.isnan(ks[curr]) or np.isnan(ts[prev]):
            return False
        return bool(ts[prev] >= ks[prev] and ts[curr] < ks[curr])

    @staticmethod
    def kumo_breakout_bullish(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close broke above Kumo cloud (above max(SpanA, SpanB))."""
        logger.info("Evaluating Ichimoku kumo_breakout_bullish at shift=%d", shift)
        c = BaseIndicator.to_numpy(close_prices)
        sa = BaseIndicator.to_numpy(senkou_span_a)
        sb = BaseIndicator.to_numpy(senkou_span_b)
        curr = len(c) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(c) or curr >= len(sa) or curr >= len(sb):
            return False
        if np.isnan(sa[curr]) or np.isnan(sb[curr]):
            return False

        cloud_top_curr = max(sa[curr], sb[curr])
        cloud_top_prev = max(sa[prev], sb[prev])
        return bool(c[prev] <= cloud_top_prev and c[curr] > cloud_top_curr)

    @staticmethod
    def kumo_breakout_bearish(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Close broke below Kumo cloud (below min(SpanA, SpanB))."""
        logger.info("Evaluating Ichimoku kumo_breakout_bearish at shift=%d", shift)
        c = BaseIndicator.to_numpy(close_prices)
        sa = BaseIndicator.to_numpy(senkou_span_a)
        sb = BaseIndicator.to_numpy(senkou_span_b)
        curr = len(c) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(c) or curr >= len(sa) or curr >= len(sb):
            return False
        if np.isnan(sa[curr]) or np.isnan(sb[curr]):
            return False

        cloud_bottom_curr = min(sa[curr], sb[curr])
        cloud_bottom_prev = min(sa[prev], sb[prev])
        return bool(c[prev] >= cloud_bottom_prev and c[curr] < cloud_bottom_curr)

    @staticmethod
    def senkou_span_cross_bullish(
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Senkou Span A crossed above Senkou Span B."""
        logger.info("Evaluating Ichimoku senkou_span_cross_bullish at shift=%d", shift)
        sa = BaseIndicator.to_numpy(senkou_span_a)
        sb = BaseIndicator.to_numpy(senkou_span_b)
        curr = len(sa) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(sa) or curr >= len(sb):
            return False
        if np.isnan(sa[curr]) or np.isnan(sb[curr]) or np.isnan(sa[prev]):
            return False
        return bool(sa[prev] <= sb[prev] and sa[curr] > sb[curr])

    @staticmethod
    def senkou_span_cross_bearish(
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
    ) -> bool:
        """Check if Senkou Span A crossed below Senkou Span B."""
        logger.info("Evaluating Ichimoku senkou_span_cross_bearish at shift=%d", shift)
        sa = BaseIndicator.to_numpy(senkou_span_a)
        sb = BaseIndicator.to_numpy(senkou_span_b)
        curr = len(sa) - 1 - shift
        prev = curr - 1
        if prev < 0 or curr >= len(sa) or curr >= len(sb):
            return False
        if np.isnan(sa[curr]) or np.isnan(sb[curr]) or np.isnan(sa[prev]):
            return False
        return bool(sa[prev] >= sb[prev] and sa[curr] < sb[curr])
