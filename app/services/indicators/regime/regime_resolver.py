"""Multi-Factor Market Regime Resolver Indicator Block.

Description:
    Synthesizes directional strength (ADX/DMI), choppiness index, and price
    channel breakouts into a unified quantitative regime classification state:
    1.0: TRANSITION, 2.0: RANGE, 3.0: CHOPPY_RANGE, 4.0: TREND_UP,
    5.0: TREND_DOWN, 6.0: BREAKOUT_UP, 7.0: BREAKOUT_DOWN,
    8.0: LOW_LIQUIDITY, 9.0: UNSTABLE.

Purpose:
    FEAT-SERVICES-INDICATOR-REGIMERESOLVER

Key Capabilities:
    - FR-SERVICES-REGIMERESOLVER-CALCULATE: Fuses multi-indicator inputs into series.
    - FR-SERVICES-REGIMERESOLVER-CONDITIONS: Evaluates uptrend, range, and breakouts.

Python API Usage:
    ```python
    from app.services.indicators.regime.regime_resolver import MarketRegimeResolver

    res = MarketRegimeResolver.calculate(high, low, close)
    regime = res["regime"]
    confidence = res["confidence"]

    uptrend = MarketRegimeResolver.is_uptrend(regime, shift=0)
    ranging = MarketRegimeResolver.is_ranging(regime, shift=0)
    ```

CLI Usage:
    N/A (Analytical block module invoked by strategy authoring and engine runners).
"""

from typing import Any, override

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import BaseIndicator, IndicatorSeries
from app.services.indicators.regime.choppiness import ChoppinessIndex
from app.services.indicators.trend.adx import ADX

logger = get_logger(__name__)

REGIME_TRANSITION: float = 1.0
REGIME_RANGE: float = 2.0
REGIME_CHOPPY_RANGE: float = 3.0
REGIME_TREND_UP: float = 4.0
REGIME_TREND_DOWN: float = 5.0
REGIME_BREAKOUT_UP: float = 6.0
REGIME_BREAKOUT_DOWN: float = 7.0
REGIME_LOW_LIQUIDITY: float = 8.0
REGIME_UNSTABLE: float = 9.0

DEFAULT_ADX_PERIOD: int = 14
DEFAULT_ADX_THRESHOLD: float = 25.0
WEAK_TREND_ADX: float = 20.0
DEFAULT_CHOP_PERIOD: int = 14
DEFAULT_CHOP_LOWER: float = 38.2
DEFAULT_CHOP_UPPER: float = 61.8
DEFAULT_DONCHIAN_PERIOD: int = 20
BREAKOUT_CONFIDENCE: float = 0.85
RANGE_CONFIDENCE: float = 0.70
TRANSITION_CONFIDENCE: float = 0.50


class MarketRegimeResolver(BaseIndicator):
    """Multi-factor market regime resolver and confidence estimator."""

    @classmethod
    @override
    def calculate(
        cls,
        high: IndicatorSeries | np.ndarray[Any, Any],
        low: IndicatorSeries | np.ndarray[Any, Any],
        close: IndicatorSeries | np.ndarray[Any, Any],
        volume: IndicatorSeries | np.ndarray[Any, Any] | None = None,
        adx_period: int = DEFAULT_ADX_PERIOD,
        adx_threshold: float = DEFAULT_ADX_THRESHOLD,
        chop_period: int = DEFAULT_CHOP_PERIOD,
        chop_lower: float = DEFAULT_CHOP_LOWER,
        chop_upper: float = DEFAULT_CHOP_UPPER,
        donchian_period: int = DEFAULT_DONCHIAN_PERIOD,
    ) -> dict[str, IndicatorSeries]:
        """Resolve unified market regime classification and confidence.

        Args:
            high: High price series.
            low: Low price series.
            close: Close price series.
            volume: Optional volume series.
            adx_period: ADX lookback period.
            adx_threshold: Strong trend threshold for ADX.
            chop_period: Choppiness Index lookback period.
            chop_lower: Directional threshold for Choppiness.
            chop_upper: Choppy threshold for Choppiness.
            donchian_period: Channel breakout period.

        Returns:
            Dictionary with 'regime' and 'confidence' IndicatorSeries.
        """
        logger.info(
            "MarketRegimeResolver initiated: adx=%d, chop=%d, donchian=%d",
            adx_period,
            chop_period,
            donchian_period,
        )
        h_arr = cls.to_numpy(high)
        l_arr = cls.to_numpy(low)
        c_arr = cls.to_numpy(close)
        n = len(c_arr)
        if n == 0 or len(h_arr) != n or len(l_arr) != n:
            raise ValueError(
                "High, Low, and Close arrays cannot be empty and lengths must match"
            )

        # Sub-indicators
        adx_dict = ADX.calculate(h_arr, l_arr, c_arr, period=adx_period)
        adx_vals = adx_dict["main"].values
        pdi_vals = adx_dict["di_plus"].values
        mdi_vals = adx_dict["di_minus"].values

        chop_dict = ChoppinessIndex.calculate(
            h_arr,
            l_arr,
            c_arr,
            period=chop_period,
            lower_threshold=chop_lower,
            upper_threshold=chop_upper,
        )
        chop_vals = chop_dict["chop"].values

        regime_vals, conf_vals = cls._resolve_regimes(
            prices=(h_arr, l_arr, c_arr),
            adx_data=(adx_vals, pdi_vals, mdi_vals),
            chop_vals=chop_vals,
            adx_thresh=adx_threshold,
            chop_bounds=(chop_lower, chop_upper),
            donchian_period=donchian_period,
        )

        return {
            "regime": IndicatorSeries(regime_vals, name="MarketRegime"),
            "confidence": IndicatorSeries(conf_vals, name="RegimeConfidence"),
        }

    @classmethod
    def _resolve_regimes(
        cls,
        *,
        prices: tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]],
        adx_data: tuple[
            np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]
        ],
        chop_vals: np.ndarray[Any, Any],
        adx_thresh: float,
        chop_bounds: tuple[float, float],
        donchian_period: int,
    ) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
        h_arr, l_arr, c_arr = prices
        adx_vals, pdi_vals, mdi_vals = adx_data
        chop_lower, chop_upper = chop_bounds
        n = len(c_arr)
        regime = np.full(n, REGIME_TRANSITION, dtype=np.float64)
        confidence = np.full(n, TRANSITION_CONFIDENCE, dtype=np.float64)

        for i in range(n):
            c = c_arr[i]
            adx = adx_vals[i]
            pdi = pdi_vals[i]
            mdi = mdi_vals[i]
            chop = chop_vals[i]

            start = max(0, i - donchian_period)
            upper_band = float(np.max(h_arr[start:i])) if i > 0 else h_arr[0]
            lower_band = float(np.min(l_arr[start:i])) if i > 0 else l_arr[0]

            r, conf = cls._classify_single_bar(
                c=c,
                bands=(upper_band, lower_band),
                dmi=(adx, pdi, mdi),
                chop=chop,
                thresholds=(adx_thresh, chop_lower, chop_upper),
            )
            regime[i] = r
            confidence[i] = conf

        return regime, confidence

    @staticmethod
    def _classify_single_bar(
        *,
        c: float,
        bands: tuple[float, float],
        dmi: tuple[float, float, float],
        chop: float,
        thresholds: tuple[float, float, float],
    ) -> tuple[float, float]:
        """Classify a single bar into regime and confidence score."""
        upper_band, lower_band = bands
        adx, pdi, mdi = dmi
        adx_thresh, chop_lower, chop_upper = thresholds

        # Priority 1: Donchian Channel Breakouts
        if upper_band > 0.0 and c >= upper_band:
            return REGIME_BREAKOUT_UP, BREAKOUT_CONFIDENCE
        if lower_band > 0.0 and c <= lower_band:
            return REGIME_BREAKOUT_DOWN, BREAKOUT_CONFIDENCE

        # Priority 2: Strong Trend
        if not np.isnan(adx) and (adx >= adx_thresh or chop <= chop_lower):
            reg = REGIME_TREND_UP if pdi > mdi else REGIME_TREND_DOWN
            return reg, min(1.0, max(0.5, adx / 50.0))

        # Priority 3: Choppy / Range
        if chop >= chop_upper:
            return REGIME_CHOPPY_RANGE, min(1.0, chop / 100.0)
        if not np.isnan(adx) and adx < WEAK_TREND_ADX:
            return REGIME_RANGE, RANGE_CONFIDENCE

        return REGIME_TRANSITION, TRANSITION_CONFIDENCE

    @classmethod
    def is_uptrend(cls, regime: IndicatorSeries, shift: int = 0) -> bool:
        """True if market is in uptrend or upward breakout."""
        logger.info("Evaluating MarketRegimeResolver is_uptrend at shift=%d", shift)
        val = regime.get(shift)
        return not np.isnan(val) and val in (REGIME_TREND_UP, REGIME_BREAKOUT_UP)

    @classmethod
    def is_downtrend(cls, regime: IndicatorSeries, shift: int = 0) -> bool:
        """True if market is in downtrend or downward breakout."""
        logger.info("Evaluating MarketRegimeResolver is_downtrend at shift=%d", shift)
        val = regime.get(shift)
        return not np.isnan(val) and val in (REGIME_TREND_DOWN, REGIME_BREAKOUT_DOWN)

    @classmethod
    def is_ranging(cls, regime: IndicatorSeries, shift: int = 0) -> bool:
        """True if market is ranging or in choppy consolidation."""
        logger.info("Evaluating MarketRegimeResolver is_ranging at shift=%d", shift)
        val = regime.get(shift)
        return not np.isnan(val) and val in (REGIME_RANGE, REGIME_CHOPPY_RANGE)

    @classmethod
    def is_breakout(cls, regime: IndicatorSeries, shift: int = 0) -> bool:
        """True if market is breaking out above or below channels."""
        logger.info("Evaluating MarketRegimeResolver is_breakout at shift=%d", shift)
        val = regime.get(shift)
        return not np.isnan(val) and val in (REGIME_BREAKOUT_UP, REGIME_BREAKOUT_DOWN)
