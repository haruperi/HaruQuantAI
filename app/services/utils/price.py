"""Single-bar, Quote, Multi-timeframe, Session, and Heiken Ashi price blocks.

Description:
    Provides consolidated price building blocks matching StrategyQuant X:
    - BarPrice: Single-bar OHLCV queries and vectorized IndicatorSeries.
    - QuotePrice: Bid, Ask, Spread (points), and SpreadInPips calculations.
    - MTFPrice: Multi-timeframe bar resampling (Daily, Weekly, Monthly OHLC).
    - SessionPrice: Intraday session window aggregator (SessionOpen/High/Low/Close).
    - HeikenAshiPrice: Filtered Heiken Ashi candle price feeds.

Purpose:
    FEAT-SERVICES-PRICE: Comprehensive price primitive building blocks.

Key Capabilities:
    - FR-SERVICES-BAR-PRICE-SERIES: Single-bar OHLCV primitives and series.
      Associated: `BarPrice.open()`, `BarPrice.high()`, `BarPrice.low()`,
      `BarPrice.close()`, `BarPrice.volume()`, and series accessors.
      Logging: DEBUG on point evaluation, INFO on series export.
    - FR-SERVICES-QUOTE-PRICE-SPREAD: Bid, ask, and spread calculation in points/pips.
      Associated: `QuotePrice.bid()`, `QuotePrice.ask()`, `QuotePrice.spread()`,
      `QuotePrice.spread_in_pips()`, and series accessors.
      Logging: DEBUG on quote queries, INFO on spread series exports.
    - FR-SERVICES-MTF-PRICE-DAILY: Multi-timeframe Daily OHLC resampled bar access.
      Associated: `MTFPrice.daily_open()`, `MTFPrice.daily_high()`,
      `MTFPrice.daily_low()`, `MTFPrice.daily_close()`, `MTFPrice.daily_close_series()`.
      Logging: DEBUG on queries, INFO on series export.
    - FR-SERVICES-MTF-PRICE-WEEKLY: Multi-timeframe Weekly OHLC resampled bar access.
      Associated: `MTFPrice.weekly_open()`, `MTFPrice.weekly_high()`,
      `MTFPrice.weekly_low()`, `MTFPrice.weekly_close()`,
      `MTFPrice.weekly_close_series()`.
      Logging: DEBUG on queries, INFO on series export.
    - FR-SERVICES-MTF-PRICE-MONTHLY: Multi-timeframe Monthly OHLC resampled bar access.
      Associated: `MTFPrice.monthly_open()`, `MTFPrice.monthly_high()`,
      `MTFPrice.monthly_low()`, `MTFPrice.monthly_close()`,
      `MTFPrice.monthly_close_series()`.
      Logging: DEBUG on queries, INFO on series export.
    - FR-SERVICES-SESSION-PRICE-WINDOW: Intraday session window aggregation and shifts.
      Associated: `SessionPrice.open()`, `SessionPrice.high()`,
      `SessionPrice.low()`, `SessionPrice.close()`, and series accessors.
      Logging: DEBUG on queries and session aggregation.
    - FR-SERVICES-HEIKEN-ASHI-PRICE: Smoothed Heiken Ashi candle price calculations.
      Associated: `HeikenAshiPrice.open()`, `HeikenAshiPrice.high()`,
      `HeikenAshiPrice.low()`, `HeikenAshiPrice.close()`, and series accessors.
      Logging: DEBUG on queries, INFO on series export.

Python API Usage:
    ```python
    import numpy as np
    from app.services.utils.price import (
        BarPrice,
        HeikenAshiPrice,
        MTFPrice,
        QuotePrice,
        SessionPrice,
    )

    o = np.array([100.0, 102.0, 105.0])
    h = np.array([103.0, 106.0, 108.0])
    l = np.array([99.0, 101.0, 104.0])
    c = np.array([102.0, 105.0, 107.0])
    bp = BarPrice(o, h, l, c)
    curr_c = bp.close(shift=0)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_price.py --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import IndicatorSeries
from app.services.indicators.price_action.heiken_ashi import HeikenAshi
from app.services.utils.bar_time import normalize_timestamps

logger = get_logger(__name__)

DEFAULT_PIP_SIZE: float = 0.0001
SECONDS_IN_MINUTE: int = 60
SECONDS_IN_HOUR: int = 3600
MINUTES_IN_HOUR: int = 60
HOURS_IN_DAY: int = 24

_normalize_timestamps = normalize_timestamps


class BarPrice:
    """OHLCV price block wrapping price arrays with historical bar shifts."""

    def __init__(
        self,
        open_data: np.ndarray[Any, Any] | Sequence[float],
        high_data: np.ndarray[Any, Any] | Sequence[float],
        low_data: np.ndarray[Any, Any] | Sequence[float],
        close_data: np.ndarray[Any, Any] | Sequence[float],
        volume_data: np.ndarray[Any, Any] | Sequence[float] | None = None,
    ) -> None:
        """Initialize BarPrice block with OHLC and optional Volume data.

        Args:
            open_data: Array or sequence of Open prices.
            high_data: Array or sequence of High prices.
            low_data: Array or sequence of Low prices.
            close_data: Array or sequence of Close prices.
            volume_data: Optional array or sequence of bar volumes.

        Raises:
            ValueError: If input arrays are empty or lengths do not match.
        """
        self._open = np.asarray(open_data, dtype=np.float64)
        self._high = np.asarray(high_data, dtype=np.float64)
        self._low = np.asarray(low_data, dtype=np.float64)
        self._close = np.asarray(close_data, dtype=np.float64)

        n = len(self._close)
        if n == 0:
            raise ValueError("Bar price data arrays cannot be empty.")
        if not (len(self._open) == len(self._high) == len(self._low) == n):
            raise ValueError(
                f"OHLC mismatch: O={len(self._open)}, H={len(self._high)}, "
                f"L={len(self._low)}, C={n}."
            )

        if volume_data is None:
            self._volume = np.zeros(n, dtype=np.float64)
        else:
            self._volume = np.asarray(volume_data, dtype=np.float64)
            if len(self._volume) != n:
                raise ValueError(
                    f"Volume array length ({len(self._volume)}) does not match "
                    f"price bars ({n})."
                )

        logger.debug(
            "FR-SERVICES-BAR-PRICE-SERIES: Initialized BarPrice with %d bars", n
        )

    def __len__(self) -> int:
        """Return total number of bars."""
        return len(self._close)

    def _get_value(self, arr: np.ndarray[Any, Any], shift: int) -> float:
        """Retrieve historical bar value with shift where 0 is newest bar."""
        if shift < 0 or shift >= len(arr):
            logger.debug(
                "FR-SERVICES-BAR-PRICE-SERIES: Shift %d out of bounds (len=%d)",
                shift,
                len(arr),
            )
            return float("nan")
        return float(arr[-(1 + shift)])

    def open(self, shift: int = 0) -> float:
        """Get Open price at historical shift."""
        val = self._get_value(self._open, shift)
        logger.debug("FR-SERVICES-BAR-PRICE-SERIES: Open(shift=%d) = %f", shift, val)
        return val

    def high(self, shift: int = 0) -> float:
        """Get High price at historical shift."""
        val = self._get_value(self._high, shift)
        logger.debug("FR-SERVICES-BAR-PRICE-SERIES: High(shift=%d) = %f", shift, val)
        return val

    def low(self, shift: int = 0) -> float:
        """Get Low price at historical shift."""
        val = self._get_value(self._low, shift)
        logger.debug("FR-SERVICES-BAR-PRICE-SERIES: Low(shift=%d) = %f", shift, val)
        return val

    def close(self, shift: int = 0) -> float:
        """Get Close price at historical shift."""
        val = self._get_value(self._close, shift)
        logger.debug("FR-SERVICES-BAR-PRICE-SERIES: Close(shift=%d) = %f", shift, val)
        return val

    def volume(self, shift: int = 0) -> float:
        """Get Volume at historical shift."""
        val = self._get_value(self._volume, shift)
        logger.debug("FR-SERVICES-BAR-PRICE-SERIES: Volume(shift=%d) = %f", shift, val)
        return val

    def open_series(self) -> IndicatorSeries:
        """Return Open series wrapped as an IndicatorSeries."""
        logger.info("FR-SERVICES-BAR-PRICE-SERIES: Exporting Open IndicatorSeries")
        return IndicatorSeries(self._open, name="Open")

    def high_series(self) -> IndicatorSeries:
        """Return High series wrapped as an IndicatorSeries."""
        logger.info("FR-SERVICES-BAR-PRICE-SERIES: Exporting High IndicatorSeries")
        return IndicatorSeries(self._high, name="High")

    def low_series(self) -> IndicatorSeries:
        """Return Low series wrapped as an IndicatorSeries."""
        logger.info("FR-SERVICES-BAR-PRICE-SERIES: Exporting Low IndicatorSeries")
        return IndicatorSeries(self._low, name="Low")

    def close_series(self) -> IndicatorSeries:
        """Return Close series wrapped as an IndicatorSeries."""
        logger.info("FR-SERVICES-BAR-PRICE-SERIES: Exporting Close IndicatorSeries")
        return IndicatorSeries(self._close, name="Close")

    def volume_series(self) -> IndicatorSeries:
        """Return Volume series wrapped as an IndicatorSeries."""
        logger.info("FR-SERVICES-BAR-PRICE-SERIES: Exporting Volume IndicatorSeries")
        return IndicatorSeries(self._volume, name="Volume")


class QuotePrice:
    """Quote price block wrapping Bid and Ask data with spread calculations."""

    def __init__(
        self,
        bid: np.ndarray[Any, Any] | Sequence[float],
        ask: np.ndarray[Any, Any] | Sequence[float],
        pip_size: float = DEFAULT_PIP_SIZE,
    ) -> None:
        """Initialize QuotePrice block.

        Args:
            bid: Array or sequence of Bid prices.
            ask: Array or sequence of Ask prices.
            pip_size: Size of 1 pip for currency or instrument (default 0.0001).

        Raises:
            ValueError: If arrays are empty, lengths mismatch, or pip_size <= 0.
        """
        self._bid = np.asarray(bid, dtype=np.float64)
        self._ask = np.asarray(ask, dtype=np.float64)

        if len(self._bid) == 0:
            raise ValueError("Quote price arrays cannot be empty.")
        if len(self._bid) != len(self._ask):
            raise ValueError(
                f"Bid length ({len(self._bid)}) does not match Ask length "
                f"({len(self._ask)})."
            )
        if pip_size <= 0.0:
            raise ValueError(f"pip_size must be strictly positive, got {pip_size}.")

        self._pip_size = float(pip_size)
        logger.debug(
            "FR-SERVICES-QUOTE-PRICE-SPREAD: Init QuotePrice (%d bars, pip=%f)",
            len(self._bid),
            self._pip_size,
        )

    def __len__(self) -> int:
        """Return total number of quotes."""
        return len(self._bid)

    @property
    def pip_size(self) -> float:
        """Return instrument pip size."""
        return self._pip_size

    def _get_val(self, arr: np.ndarray[Any, Any], shift: int) -> float:
        """Retrieve historical quote value with shift where 0 is newest."""
        if shift < 0 or shift >= len(arr):
            logger.debug(
                "FR-SERVICES-QUOTE-PRICE-SPREAD: Shift %d out of bounds (len=%d)",
                shift,
                len(arr),
            )
            return float("nan")
        return float(arr[-(1 + shift)])

    def bid(self, shift: int = 0) -> float:
        """Get Bid price at historical shift."""
        val = self._get_val(self._bid, shift)
        logger.debug("FR-SERVICES-QUOTE-PRICE-SPREAD: Bid(shift=%d) = %f", shift, val)
        return val

    def ask(self, shift: int = 0) -> float:
        """Get Ask price at historical shift."""
        val = self._get_val(self._ask, shift)
        logger.debug("FR-SERVICES-QUOTE-PRICE-SPREAD: Ask(shift=%d) = %f", shift, val)
        return val

    def spread(self, shift: int = 0) -> float:
        """Get raw spread (Ask - Bid in points) at historical shift."""
        b = self.bid(shift)
        a = self.ask(shift)
        if np.isnan(b) or np.isnan(a):
            return float("nan")
        spread_val = float(abs(a - b))
        logger.debug(
            "FR-SERVICES-QUOTE-PRICE-SPREAD: Spread(shift=%d) = %f", shift, spread_val
        )
        return spread_val

    def spread_in_pips(self, shift: int = 0, pip_size: float | None = None) -> float:
        """Get spread converted to pips at historical shift."""
        pts = self.spread(shift)
        if np.isnan(pts):
            return float("nan")
        effective_pip_size = self._pip_size if pip_size is None else pip_size
        if effective_pip_size <= 0.0:
            return float("nan")
        pips = float(pts / effective_pip_size)
        logger.debug(
            "FR-SERVICES-QUOTE-PRICE-SPREAD: SpreadInPips(shift=%d) = %f pips",
            shift,
            pips,
        )
        return pips

    def bid_series(self) -> IndicatorSeries:
        """Return Bid series as an IndicatorSeries."""
        return IndicatorSeries(self._bid, name="Bid")

    def ask_series(self) -> IndicatorSeries:
        """Return Ask series as an IndicatorSeries."""
        return IndicatorSeries(self._ask, name="Ask")

    def spread_series(self) -> IndicatorSeries:
        """Return raw spread series as an IndicatorSeries."""
        logger.info("FR-SERVICES-QUOTE-PRICE-SPREAD: Exporting Spread series")
        return IndicatorSeries(np.abs(self._ask - self._bid), name="Spread")

    def spread_in_pips_series(self, pip_size: float | None = None) -> IndicatorSeries:
        """Return spread-in-pips series as an IndicatorSeries."""
        effective_pip_size = self._pip_size if pip_size is None else pip_size
        logger.info(
            "FR-SERVICES-QUOTE-PRICE-SPREAD: Exporting SpreadInPips (pip=%f)",
            effective_pip_size,
        )
        pips_arr = np.abs(self._ask - self._bid) / effective_pip_size
        return IndicatorSeries(pips_arr, name="SpreadInPips")


class MTFPrice:
    """Multi-timeframe price aggregator for Daily, Weekly, and Monthly OHLC bars."""

    def __init__(
        self,
        timestamps: np.ndarray[Any, Any] | Sequence[Any],
        open_data: np.ndarray[Any, Any] | Sequence[float],
        high_data: np.ndarray[Any, Any] | Sequence[float],
        low_data: np.ndarray[Any, Any] | Sequence[float],
        close_data: np.ndarray[Any, Any] | Sequence[float],
    ) -> None:
        """Initialize MTFPrice with timestamps and OHLC data.

        Args:
            timestamps: Array or sequence of bar timestamps.
            open_data: Array or sequence of Open prices.
            high_data: Array or sequence of High prices.
            low_data: Array or sequence of Low prices.
            close_data: Array or sequence of Close prices.

        Raises:
            ValueError: If arrays are empty or lengths mismatch.
        """
        self._ts = _normalize_timestamps(timestamps)
        self._open = np.asarray(open_data, dtype=np.float64)
        self._high = np.asarray(high_data, dtype=np.float64)
        self._low = np.asarray(low_data, dtype=np.float64)
        self._close = np.asarray(close_data, dtype=np.float64)

        n = len(self._ts)
        if n == 0:
            raise ValueError("MTF price data arrays cannot be empty.")
        if not (
            len(self._open)
            == len(self._high)
            == len(self._low)
            == len(self._close)
            == n
        ):
            raise ValueError("All OHLC and timestamp arrays must have equal length.")

        self._build_aggregates()
        logger.debug(
            "FR-SERVICES-MTF-PRICE-DAILY: Initialized MTFPrice (%d base bars -> "
            "%d daily, %d weekly, %d monthly)",
            n,
            len(self._d_close),
            len(self._w_close),
            len(self._m_close),
        )

    def _build_aggregates(self) -> None:
        """Resample bars into daily, weekly, and monthly OHLC arrays."""
        d_groups: dict[tuple[int, int, int], list[int]] = {}
        w_groups: dict[tuple[int, int], list[int]] = {}
        m_groups: dict[tuple[int, int], list[int]] = {}

        for i, ts in enumerate(self._ts):
            dt = datetime.fromtimestamp(ts, tz=UTC)
            d_key = (dt.year, dt.month, dt.day)
            iso_year, iso_week, _ = dt.isocalendar()
            w_key = (iso_year, iso_week)
            m_key = (dt.year, dt.month)

            d_groups.setdefault(d_key, []).append(i)
            w_groups.setdefault(w_key, []).append(i)
            m_groups.setdefault(m_key, []).append(i)

        self._d_open, self._d_high, self._d_low, self._d_close = self._aggregate(
            d_groups
        )
        self._w_open, self._w_high, self._w_low, self._w_close = self._aggregate(
            w_groups
        )
        self._m_open, self._m_high, self._m_low, self._m_close = self._aggregate(
            m_groups
        )

    def _aggregate(
        self, groups: dict[Any, list[int]]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Aggregate grouped indices into OHLC arrays ordered chronologically."""
        opens: list[float] = []
        highs: list[float] = []
        lows: list[float] = []
        closes: list[float] = []
        for idxs in groups.values():
            opens.append(self._open[idxs[0]])
            highs.append(np.max(self._high[idxs]))
            lows.append(np.min(self._low[idxs]))
            closes.append(self._close[idxs[-1]])
        return (
            np.array(opens, dtype=np.float64),
            np.array(highs, dtype=np.float64),
            np.array(lows, dtype=np.float64),
            np.array(closes, dtype=np.float64),
        )

    def _lookup(self, arr: np.ndarray, shift: int) -> float:
        """Lookup historical bar value where shift=0 is current and 1 is previous."""
        if shift < 0 or shift >= len(arr):
            return float("nan")
        return float(arr[-(1 + shift)])

    # --- Daily Bar Lookups ---

    def daily_open(self, shift: int = 0) -> float:
        """Get Daily Open price (OpenD) at historical shift."""
        val = self._lookup(self._d_open, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-DAILY: daily_open(shift=%d) = %f", shift, val
        )
        return val

    def daily_high(self, shift: int = 0) -> float:
        """Get Daily High price (HighD) at historical shift."""
        val = self._lookup(self._d_high, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-DAILY: daily_high(shift=%d) = %f", shift, val
        )
        return val

    def daily_low(self, shift: int = 0) -> float:
        """Get Daily Low price (LowD) at historical shift."""
        val = self._lookup(self._d_low, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-DAILY: daily_low(shift=%d) = %f", shift, val
        )
        return val

    def daily_close(self, shift: int = 0) -> float:
        """Get Daily Close price (CloseD) at historical shift."""
        val = self._lookup(self._d_close, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-DAILY: daily_close(shift=%d) = %f", shift, val
        )
        return val

    # --- Weekly Bar Lookups ---

    def weekly_open(self, shift: int = 0) -> float:
        """Get Weekly Open price (OpenW) at historical shift."""
        val = self._lookup(self._w_open, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-WEEKLY: weekly_open(shift=%d) = %f", shift, val
        )
        return val

    def weekly_high(self, shift: int = 0) -> float:
        """Get Weekly High price (HighW) at historical shift."""
        val = self._lookup(self._w_high, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-WEEKLY: weekly_high(shift=%d) = %f", shift, val
        )
        return val

    def weekly_low(self, shift: int = 0) -> float:
        """Get Weekly Low price (LowW) at historical shift."""
        val = self._lookup(self._w_low, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-WEEKLY: weekly_low(shift=%d) = %f", shift, val
        )
        return val

    def weekly_close(self, shift: int = 0) -> float:
        """Get Weekly Close price (CloseW) at historical shift."""
        val = self._lookup(self._w_close, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-WEEKLY: weekly_close(shift=%d) = %f", shift, val
        )
        return val

    # --- Monthly Bar Lookups ---

    def monthly_open(self, shift: int = 0) -> float:
        """Get Monthly Open price (OpenM) at historical shift."""
        val = self._lookup(self._m_open, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-MONTHLY: monthly_open(shift=%d) = %f", shift, val
        )
        return val

    def monthly_high(self, shift: int = 0) -> float:
        """Get Monthly High price (HighM) at historical shift."""
        val = self._lookup(self._m_high, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-MONTHLY: monthly_high(shift=%d) = %f", shift, val
        )
        return val

    def monthly_low(self, shift: int = 0) -> float:
        """Get Monthly Low price (LowM) at historical shift."""
        val = self._lookup(self._m_low, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-MONTHLY: monthly_low(shift=%d) = %f", shift, val
        )
        return val

    def monthly_close(self, shift: int = 0) -> float:
        """Get Monthly Close price (CloseM) at historical shift."""
        val = self._lookup(self._m_close, shift)
        logger.debug(
            "FR-SERVICES-MTF-PRICE-MONTHLY: monthly_close(shift=%d) = %f", shift, val
        )
        return val

    # --- IndicatorSeries Exports ---

    def daily_close_series(self) -> IndicatorSeries:
        """Return Daily Close series as an IndicatorSeries."""
        logger.info("FR-SERVICES-MTF-PRICE-DAILY: Exporting daily close series")
        return IndicatorSeries(self._d_close, name="CloseD")

    def weekly_close_series(self) -> IndicatorSeries:
        """Return Weekly Close series as an IndicatorSeries."""
        logger.info("FR-SERVICES-MTF-PRICE-WEEKLY: Exporting weekly close series")
        return IndicatorSeries(self._w_close, name="CloseW")

    def monthly_close_series(self) -> IndicatorSeries:
        """Return Monthly Close series as an IndicatorSeries."""
        logger.info("FR-SERVICES-MTF-PRICE-MONTHLY: Exporting monthly close series")
        return IndicatorSeries(self._m_close, name="CloseM")


class SessionPrice:
    """Intraday trading session OHLC aggregator and shift query block."""

    def __init__(
        self,
        timestamps: np.ndarray[Any, Any] | Sequence[Any],
        open_data: np.ndarray[Any, Any] | Sequence[float],
        high_data: np.ndarray[Any, Any] | Sequence[float],
        low_data: np.ndarray[Any, Any] | Sequence[float],
        close_data: np.ndarray[Any, Any] | Sequence[float],
        *,
        start_hour: int = 0,
        start_minute: int = 0,
        end_hour: int = 23,
        end_minute: int = 59,
    ) -> None:
        """Initialize SessionPrice block with custom session hours.

        Args:
            timestamps: Array or sequence of bar timestamps.
            open_data: Array or sequence of Open prices.
            high_data: Array or sequence of High prices.
            low_data: Array or sequence of Low prices.
            close_data: Array or sequence of Close prices.
            start_hour: Session start hour (0-23).
            start_minute: Session start minute (0-59).
            end_hour: Session end hour (0-23).
            end_minute: Session end minute (0-59).

        Raises:
            ValueError: If arrays are empty, lengths mismatch, or times invalid.
        """
        self._ts = _normalize_timestamps(timestamps)
        self._open = np.asarray(open_data, dtype=np.float64)
        self._high = np.asarray(high_data, dtype=np.float64)
        self._low = np.asarray(low_data, dtype=np.float64)
        self._close = np.asarray(close_data, dtype=np.float64)

        n = len(self._ts)
        if n == 0:
            raise ValueError("Session price data arrays cannot be empty.")
        if not (
            len(self._open)
            == len(self._high)
            == len(self._low)
            == len(self._close)
            == n
        ):
            raise ValueError("All OHLC and timestamp arrays must have equal length.")

        if not (0 <= start_hour < HOURS_IN_DAY and 0 <= start_minute < MINUTES_IN_HOUR):
            raise ValueError(
                f"Invalid session start time: {start_hour}:{start_minute}."
            )
        if not (0 <= end_hour < HOURS_IN_DAY and 0 <= end_minute < MINUTES_IN_HOUR):
            raise ValueError(f"Invalid session end time: {end_hour}:{end_minute}.")

        self._start_sec = (
            start_hour * SECONDS_IN_HOUR + start_minute * SECONDS_IN_MINUTE
        )
        self._end_sec = end_hour * SECONDS_IN_HOUR + end_minute * SECONDS_IN_MINUTE
        self._cross_midnight = self._start_sec > self._end_sec

        self._build_sessions()
        logger.debug(
            "FR-SERVICES-SESSION-PRICE-WINDOW: SessionPrice (%02d:%02d-%02d:%02d) "
            "%d sessions from %d bars",
            start_hour,
            start_minute,
            end_hour,
            end_minute,
            len(self._session_close),
            n,
        )

    def _in_session(self, sod: int) -> bool:
        """Check if second-of-day falls within the session window."""
        if not self._cross_midnight:
            return self._start_sec <= sod <= self._end_sec
        return sod >= self._start_sec or sod <= self._end_sec

    def _build_sessions(self) -> None:
        """Group bars into distinct calendar sessions."""
        session_opens: list[float] = []
        session_highs: list[float] = []
        session_lows: list[float] = []
        session_closes: list[float] = []

        cur_open: float | None = None
        cur_high = -np.inf
        cur_low = np.inf
        cur_close: float | None = None
        last_day_key: tuple[int, int, int] | None = None

        for i, ts in enumerate(self._ts):
            dt = datetime.fromtimestamp(ts, tz=UTC)
            sod = dt.hour * SECONDS_IN_HOUR + dt.minute * SECONDS_IN_MINUTE + dt.second
            day_key = (dt.year, dt.month, dt.day)

            # If we crossed into a new day or session boundary
            if day_key != last_day_key and cur_open is not None:
                session_opens.append(cur_open)
                session_highs.append(cur_high)
                session_lows.append(cur_low)
                session_closes.append(cur_close if cur_close is not None else cur_open)
                cur_open = None
                cur_high = -np.inf
                cur_low = np.inf
                cur_close = None

            last_day_key = day_key

            if self._in_session(sod):
                if cur_open is None:
                    cur_open = float(self._open[i])
                cur_high = max(cur_high, float(self._high[i]))
                cur_low = min(cur_low, float(self._low[i]))
                cur_close = float(self._close[i])

        if cur_open is not None:
            session_opens.append(cur_open)
            session_highs.append(cur_high)
            session_lows.append(cur_low)
            session_closes.append(cur_close if cur_close is not None else cur_open)

        self._session_open = np.array(session_opens, dtype=np.float64)
        self._session_high = np.array(session_highs, dtype=np.float64)
        self._session_low = np.array(session_lows, dtype=np.float64)
        self._session_close = np.array(session_closes, dtype=np.float64)

    def _get(self, arr: np.ndarray, days_shift: int) -> float:
        """Lookup session price by days_shift (0=current session, 1=previous)."""
        if days_shift < 0 or days_shift >= len(arr):
            logger.debug(
                "FR-SERVICES-SESSION-PRICE-WINDOW: shift %d out of bounds (%d)",
                days_shift,
                len(arr),
            )
            return float("nan")
        return float(arr[-(1 + days_shift)])

    def open(self, days_shift: int = 0) -> float:
        """Get Session Open price at specified days shift."""
        val = self._get(self._session_open, days_shift)
        logger.debug(
            "FR-SERVICES-SESSION-PRICE-WINDOW: SessionOpen(days_shift=%d) = %f",
            days_shift,
            val,
        )
        return val

    def high(self, days_shift: int = 0) -> float:
        """Get Session High price at specified days shift."""
        val = self._get(self._session_high, days_shift)
        logger.debug(
            "FR-SERVICES-SESSION-PRICE-WINDOW: SessionHigh(days_shift=%d) = %f",
            days_shift,
            val,
        )
        return val

    def low(self, days_shift: int = 0) -> float:
        """Get Session Low price at specified days shift."""
        val = self._get(self._session_low, days_shift)
        logger.debug(
            "FR-SERVICES-SESSION-PRICE-WINDOW: SessionLow(days_shift=%d) = %f",
            days_shift,
            val,
        )
        return val

    def close(self, days_shift: int = 0) -> float:
        """Get Session Close price at specified days shift."""
        val = self._get(self._session_close, days_shift)
        logger.debug(
            "FR-SERVICES-SESSION-PRICE-WINDOW: SessionClose(days_shift=%d) = %f",
            days_shift,
            val,
        )
        return val

    def open_series(self) -> IndicatorSeries:
        """Return Session Open series as an IndicatorSeries."""
        return IndicatorSeries(self._session_open, name="SessionOpen")

    def high_series(self) -> IndicatorSeries:
        """Return Session High series as an IndicatorSeries."""
        return IndicatorSeries(self._session_high, name="SessionHigh")

    def low_series(self) -> IndicatorSeries:
        """Return Session Low series as an IndicatorSeries."""
        return IndicatorSeries(self._session_low, name="SessionLow")

    def close_series(self) -> IndicatorSeries:
        """Return Session Close series as an IndicatorSeries."""
        return IndicatorSeries(self._session_close, name="SessionClose")


class HeikenAshiPrice:
    """Heiken Ashi smoothed price block with shift-indexed lookups."""

    def __init__(
        self,
        open_data: np.ndarray[Any, Any] | Sequence[float],
        high_data: np.ndarray[Any, Any] | Sequence[float],
        low_data: np.ndarray[Any, Any] | Sequence[float],
        close_data: np.ndarray[Any, Any] | Sequence[float],
    ) -> None:
        """Initialize HeikenAshiPrice block.

        Args:
            open_data: Array or sequence of raw Open prices.
            high_data: Array or sequence of raw High prices.
            low_data: Array or sequence of raw Low prices.
            close_data: Array or sequence of raw Close prices.

        Raises:
            ValueError: If input arrays are empty or lengths mismatch.
        """
        o_arr = np.asarray(open_data, dtype=np.float64)
        h_arr = np.asarray(high_data, dtype=np.float64)
        l_arr = np.asarray(low_data, dtype=np.float64)
        c_arr = np.asarray(close_data, dtype=np.float64)

        if len(c_arr) == 0:
            raise ValueError("Heiken Ashi price data arrays cannot be empty.")
        if not (len(o_arr) == len(h_arr) == len(l_arr) == len(c_arr)):
            raise ValueError("OHLC arrays must have matching lengths.")

        res = HeikenAshi.calculate(o_arr, h_arr, l_arr, c_arr)
        self._ha_open: IndicatorSeries = res["open"]
        self._ha_high: IndicatorSeries = res["high"]
        self._ha_low: IndicatorSeries = res["low"]
        self._ha_close: IndicatorSeries = res["close"]

        logger.debug(
            "FR-SERVICES-HEIKEN-ASHI-PRICE: Initialized HeikenAshiPrice with %d bars",
            len(self._ha_close),
        )

    def __len__(self) -> int:
        """Return total bar count."""
        return len(self._ha_close)

    def open(self, shift: int = 0) -> float:
        """Get Heiken Ashi Open price at historical shift."""
        val = self._ha_open.get(shift)
        logger.debug(
            "FR-SERVICES-HEIKEN-ASHI-PRICE: HA-Open(shift=%d) = %f", shift, val
        )
        return val

    def high(self, shift: int = 0) -> float:
        """Get Heiken Ashi High price at historical shift."""
        val = self._ha_high.get(shift)
        logger.debug(
            "FR-SERVICES-HEIKEN-ASHI-PRICE: HA-High(shift=%d) = %f", shift, val
        )
        return val

    def low(self, shift: int = 0) -> float:
        """Get Heiken Ashi Low price at historical shift."""
        val = self._ha_low.get(shift)
        logger.debug("FR-SERVICES-HEIKEN-ASHI-PRICE: HA-Low(shift=%d) = %f", shift, val)
        return val

    def close(self, shift: int = 0) -> float:
        """Get Heiken Ashi Close price at historical shift."""
        val = self._ha_close.get(shift)
        logger.debug(
            "FR-SERVICES-HEIKEN-ASHI-PRICE: HA-Close(shift=%d) = %f", shift, val
        )
        return val

    def open_series(self) -> IndicatorSeries:
        """Return Heiken Ashi Open series as an IndicatorSeries."""
        logger.info("FR-SERVICES-HEIKEN-ASHI-PRICE: Exporting HA-Open series")
        return self._ha_open

    def high_series(self) -> IndicatorSeries:
        """Return Heiken Ashi High series as an IndicatorSeries."""
        logger.info("FR-SERVICES-HEIKEN-ASHI-PRICE: Exporting HA-High series")
        return self._ha_high

    def low_series(self) -> IndicatorSeries:
        """Return Heiken Ashi Low series as an IndicatorSeries."""
        logger.info("FR-SERVICES-HEIKEN-ASHI-PRICE: Exporting HA-Low series")
        return self._ha_low

    def close_series(self) -> IndicatorSeries:
        """Return Heiken Ashi Close series as an IndicatorSeries."""
        logger.info("FR-SERVICES-HEIKEN-ASHI-PRICE: Exporting HA-Close series")
        return self._ha_close


__all__ = [
    "BarPrice",
    "HeikenAshiPrice",
    "MTFPrice",
    "QuotePrice",
    "SessionPrice",
    "_normalize_timestamps",
]
