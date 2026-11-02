"""Ichimoku trend indicator strategy block.

Description:
    Calculates Ichimoku Kinko Hyo components (Tenkan-sen, Kijun-sen,
    Senkou Spans, Chikou).
Purpose:
    FEAT-INDICATORS-BLOCKS: Quantitative trend indicator library.
Key Capabilities:
    - FR-indicator-trend: Ichimoku cloud and equilibrium lines.
    - FR-indicator-logging: Non-silent calculation diagnostics.
Python API Usage:
    from app.extend.blocks.indicators.trend.ichimoku import Ichimoku
    res = Ichimoku().calculate(bars)
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_families.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar, Self, override

import numpy as np
from pydantic import Field, model_validator

from app.core.host.logging import get_logger
from app.extend.blocks.comparisons import crosses_above, crosses_below, is_lower
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.indicators.base import BaseIndicator
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.series import BarData, IndicatorSeries
from app.extend.calculators.base import to_numpy

logger = get_logger(__name__)
DEFAULT_TENKAN: int = 9
DEFAULT_KIJUN: int = 26
DEFAULT_SENKOU: int = 52
STRONG_SIGNAL_LEVEL: int = 2


class Ichimoku(BaseIndicator):
    """Ichimoku Kinko Hyo indicator block."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="indicator.trend.ichimoku",
        name="Ichimoku",
        category="trend",
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("high", PortType.SERIES, required=True),
            InputPort("low", PortType.SERIES, required=True),
            InputPort("close", PortType.SERIES, required=True),
        ),
        outputs=(
            OutputPort("tenkan_sen", PortType.SERIES),
            OutputPort("kijun_sen", PortType.SERIES),
            OutputPort("senkou_span_a", PortType.SERIES),
            OutputPort("senkou_span_b", PortType.SERIES),
            OutputPort("chikou_span", PortType.SERIES),
        ),
        required_market_inputs=("high", "low", "close"),
        parameter_search_space={
            "tenkan": {"type": "int", "min": 1, "max": 36, "default": 9},
            "kijun": {"type": "int", "min": 1, "max": 104, "default": 26},
            "senkou": {"type": "int", "min": 1, "max": 208, "default": 52},
        },
        is_causal=False,
        is_generation_eligible=False,
        required_history_lookback=78,
    )
    tenkan: int = Field(default=DEFAULT_TENKAN, ge=1)
    kijun: int = Field(default=DEFAULT_KIJUN, ge=1)
    senkou: int = Field(default=DEFAULT_SENKOU, ge=1)

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Validate domain-specific bounds before batch execution."""
        if self.tenkan < 1 or self.kijun < 1 or self.senkou < 1:
            raise ValueError("All lookback periods must be >= 1")
        return self

    @override
    def required_history(self) -> int:
        """Return the history needed before initialized outputs can be consumed."""
        return max(self.tenkan, self.kijun, self.senkou) + self.kijun

    @override
    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        """Compute named batch outputs from validated settings and market data."""
        bars.require_inputs(self.spec.required_market_inputs)
        high = bars.high
        low = bars.low
        close = bars.close
        tenkan = self.tenkan
        kijun = self.kijun
        senkou = self.senkou
        logger.info(
            "Ichimoku calculation initiated: tenkan=%d, kijun=%d, senkou=%d",
            tenkan,
            kijun,
            senkou,
            extra={"tenkan": tenkan, "kijun": kijun, "senkou": senkou},
        )
        h_arr = to_numpy(high)
        l_arr = to_numpy(low)
        c_arr = to_numpy(close)
        n = len(c_arr)
        if n == 0:
            raise ValueError("Input series cannot be empty")
        if not len(h_arr) == len(l_arr) == n:
            raise ValueError("High, Low, and Close array lengths must match")
        ts_vals, ks_vals = self._calc_tenkan_kijun(h_arr, l_arr, tenkan, kijun)
        sum_a = (ts_vals + ks_vals) / 2.0
        sa_vals, sb_vals = self._calc_senkou_spans(h_arr, l_arr, sum_a, kijun, senkou)
        cs_vals = self._calc_chikou_span(c_arr, kijun)
        logger.info("Ichimoku calculation complete: bars=%d", n, extra={"bars": n})
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
        return (ts, ks)

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
        for i in range(kijun, n):
            sa[i] = sum_a[i - kijun]
            sb[i] = sum_b[i - kijun]
        return (sa, sb)

    @staticmethod
    def _calc_chikou_span(
        c_arr: np.ndarray[Any, Any], kijun: int
    ) -> np.ndarray[Any, Any]:
        n = len(c_arr)
        cs = np.full(n, np.nan, dtype=np.float64)
        for i in range(n - kijun):
            cs[i] = c_arr[i + kijun]
        return cs

    @staticmethod
    def _check_strength_bullish(
        ref_val: float,
        sa: np.ndarray[Any, Any] | None,
        sb: np.ndarray[Any, Any] | None,
        curr: int,
        signal_strength: int,
    ) -> bool:
        if sa is None or sb is None or signal_strength <= 0:
            return True
        if (
            curr >= len(sa)
            or curr >= len(sb)
            or np.isnan(sa[curr])
            or np.isnan(sb[curr])
        ):
            return False
        kumo_top = float(max(sa[curr], sb[curr]))
        kumo_bottom = float(min(sa[curr], sb[curr]))
        if signal_strength >= STRONG_SIGNAL_LEVEL:
            return ref_val > kumo_top
        return ref_val > kumo_bottom

    @staticmethod
    def _check_strength_bearish(
        ref_val: float,
        sa: np.ndarray[Any, Any] | None,
        sb: np.ndarray[Any, Any] | None,
        curr: int,
        signal_strength: int,
    ) -> bool:
        if sa is None or sb is None or signal_strength <= 0:
            return True
        if (
            curr >= len(sa)
            or curr >= len(sb)
            or np.isnan(sa[curr])
            or np.isnan(sb[curr])
        ):
            return False
        kumo_top = float(max(sa[curr], sb[curr]))
        kumo_bottom = float(min(sa[curr], sb[curr]))
        if signal_strength >= STRONG_SIGNAL_LEVEL:
            return ref_val < kumo_bottom
        return ref_val < kumo_top

    @staticmethod
    def kijun_sen_cross_bullish(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        kijun_sen: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        *,
        signal_strength: int = 0,
        shift: int = 0,
    ) -> bool:
        """Check if bar crossed bullishly across Kijun-sen (`Open < Kijun < Close`)."""
        logger.info("Evaluating Ichimoku kijun_sen_cross_bullish at shift=%d", shift)
        ks = to_numpy(kijun_sen)
        c = to_numpy(close_prices)
        curr = len(c) - 1 - shift
        if curr < 0 or curr >= len(ks) or np.isnan(ks[curr]):
            return False
        signal = is_lower(
            open_prices, kijun_sen, shift1=shift, shift2=shift, round_digits=8
        ) and is_greater(
            close_prices, kijun_sen, shift1=shift, shift2=shift, round_digits=8
        )
        if not signal:
            return False
        sa = to_numpy(senkou_span_a) if senkou_span_a is not None else None
        sb = to_numpy(senkou_span_b) if senkou_span_b is not None else None
        return Ichimoku._check_strength_bullish(
            float(ks[curr]), sa, sb, curr, signal_strength
        )

    @staticmethod
    def kijun_sen_cross_bearish(
        open_prices: IndicatorSeries | np.ndarray[Any, Any],
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        kijun_sen: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        *,
        signal_strength: int = 0,
        shift: int = 0,
    ) -> bool:
        """Check if bar crossed bearishly across Kijun-sen (`Open > Kijun > Close`)."""
        logger.info("Evaluating Ichimoku kijun_sen_cross_bearish at shift=%d", shift)
        ks = to_numpy(kijun_sen)
        c = to_numpy(close_prices)
        curr = len(c) - 1 - shift
        if curr < 0 or curr >= len(ks) or np.isnan(ks[curr]):
            return False
        signal = is_greater(
            open_prices, kijun_sen, shift1=shift, shift2=shift, round_digits=8
        ) and is_lower(
            close_prices, kijun_sen, shift1=shift, shift2=shift, round_digits=8
        )
        if not signal:
            return False
        sa = to_numpy(senkou_span_a) if senkou_span_a is not None else None
        sb = to_numpy(senkou_span_b) if senkou_span_b is not None else None
        return Ichimoku._check_strength_bearish(
            float(ks[curr]), sa, sb, curr, signal_strength
        )

    @staticmethod
    def tenkan_kijun_cross_bullish(
        tenkan_sen: IndicatorSeries | np.ndarray[Any, Any],
        kijun_sen: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
        *,
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        signal_strength: int = 0,
    ) -> bool:
        """Check if Tenkan-sen crossed above Kijun-sen."""
        logger.info("Evaluating Ichimoku tenkan_kijun_cross_bullish at shift=%d", shift)
        if not crosses_above(tenkan_sen, kijun_sen, shift=shift, round_digits=8):
            return False
        ks = to_numpy(kijun_sen)
        curr = len(ks) - 1 - shift
        sa = to_numpy(senkou_span_a) if senkou_span_a is not None else None
        sb = to_numpy(senkou_span_b) if senkou_span_b is not None else None
        return Ichimoku._check_strength_bullish(
            float(ks[curr]), sa, sb, curr, signal_strength
        )

    @staticmethod
    def tenkan_kijun_cross_bearish(
        tenkan_sen: IndicatorSeries | np.ndarray[Any, Any],
        kijun_sen: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
        *,
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        signal_strength: int = 0,
    ) -> bool:
        """Check if Tenkan-sen crossed below Kijun-sen."""
        logger.info("Evaluating Ichimoku tenkan_kijun_cross_bearish at shift=%d", shift)
        if not crosses_below(tenkan_sen, kijun_sen, shift=shift, round_digits=8):
            return False
        ks = to_numpy(kijun_sen)
        curr = len(ks) - 1 - shift
        sa = to_numpy(senkou_span_a) if senkou_span_a is not None else None
        sb = to_numpy(senkou_span_b) if senkou_span_b is not None else None
        return Ichimoku._check_strength_bearish(
            float(ks[curr]), sa, sb, curr, signal_strength
        )

    @staticmethod
    def kumo_breakout_bullish(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
        *,
        open_prices: IndicatorSeries | np.ndarray[Any, Any] | None = None,
    ) -> bool:
        """Check if price broke above Kumo cloud (above max(SpanA, SpanB))."""
        logger.info("Evaluating Ichimoku kumo_breakout_bullish at shift=%d", shift)
        c = to_numpy(close_prices)
        sa = to_numpy(senkou_span_a)
        sb = to_numpy(senkou_span_b)
        curr = len(c) - 1 - shift
        if curr < 0 or curr >= len(c) or curr >= len(sa) or (curr >= len(sb)):
            return False
        if np.isnan(sa[curr]) or np.isnan(sb[curr]) or np.isnan(c[curr]):
            return False
        cloud_top_curr = float(max(sa[curr], sb[curr]))
        if open_prices is not None:
            return is_lower(
                open_prices, cloud_top_curr, shift1=shift, round_digits=8
            ) and is_greater(close_prices, cloud_top_curr, shift1=shift, round_digits=8)
        prev = curr - 1
        if prev < 0 or np.isnan(sa[prev]) or np.isnan(sb[prev]):
            return False
        cloud_top = np.maximum(sa, sb)
        return crosses_above(close_prices, cloud_top, shift=shift, round_digits=8)

    @staticmethod
    def kumo_breakout_bearish(
        close_prices: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
        *,
        open_prices: IndicatorSeries | np.ndarray[Any, Any] | None = None,
    ) -> bool:
        """Check if price broke below Kumo cloud (below min(SpanA, SpanB))."""
        logger.info("Evaluating Ichimoku kumo_breakout_bearish at shift=%d", shift)
        c = to_numpy(close_prices)
        sa = to_numpy(senkou_span_a)
        sb = to_numpy(senkou_span_b)
        curr = len(c) - 1 - shift
        if curr < 0 or curr >= len(c) or curr >= len(sa) or (curr >= len(sb)):
            return False
        if np.isnan(sa[curr]) or np.isnan(sb[curr]) or np.isnan(c[curr]):
            return False
        cloud_bottom_curr = float(min(sa[curr], sb[curr]))
        if open_prices is not None:
            return is_greater(
                open_prices, cloud_bottom_curr, shift1=shift, round_digits=8
            ) and is_lower(
                close_prices, cloud_bottom_curr, shift1=shift, round_digits=8
            )
        prev = curr - 1
        if prev < 0 or np.isnan(sa[prev]) or np.isnan(sb[prev]):
            return False
        cloud_bottom = np.minimum(sa, sb)
        return crosses_below(close_prices, cloud_bottom, shift=shift, round_digits=8)

    @staticmethod
    def senkou_span_cross_bullish(
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
        *,
        close_prices: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        signal_strength: int = 0,
    ) -> bool:
        """Check if Senkou Span A crossed above Senkou Span B."""
        logger.info("Evaluating Ichimoku senkou_span_cross_bullish at shift=%d", shift)
        if not crosses_above(senkou_span_a, senkou_span_b, shift=shift, round_digits=8):
            return False
        if close_prices is not None and signal_strength > 0:
            sa = to_numpy(senkou_span_a)
            sb = to_numpy(senkou_span_b)
            c = to_numpy(close_prices)
            curr = len(sa) - 1 - shift
            if curr >= len(c) or np.isnan(c[curr]):
                return False
            return Ichimoku._check_strength_bullish(
                float(c[curr]), sa, sb, curr, signal_strength
            )
        return True

    @staticmethod
    def senkou_span_cross_bearish(
        senkou_span_a: IndicatorSeries | np.ndarray[Any, Any],
        senkou_span_b: IndicatorSeries | np.ndarray[Any, Any],
        shift: int = 0,
        *,
        close_prices: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        signal_strength: int = 0,
    ) -> bool:
        """Check if Senkou Span A crossed below Senkou Span B."""
        logger.info("Evaluating Ichimoku senkou_span_cross_bearish at shift=%d", shift)
        if not crosses_below(senkou_span_a, senkou_span_b, shift=shift, round_digits=8):
            return False
        if close_prices is not None and signal_strength > 0:
            sa = to_numpy(senkou_span_a)
            sb = to_numpy(senkou_span_b)
            c = to_numpy(close_prices)
            curr = len(sa) - 1 - shift
            if curr >= len(c) or np.isnan(c[curr]):
                return False
            return Ichimoku._check_strength_bearish(
                float(c[curr]), sa, sb, curr, signal_strength
            )
        return True
