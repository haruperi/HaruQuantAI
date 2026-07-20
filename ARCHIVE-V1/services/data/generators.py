"""Signal-aware tick generation from real market data for backtesting.

Purpose:
    Reconstruct tick streams from caller-provided real bars or ticks using
    canonical tick-generation models.

Classes and functions:
    TicksGenerator: Generate standardized tick DataFrames.
    generate_ticks: Generate ticks as a DataFrame.
    generate_ticks_to_parquet: Stream generated ticks to Parquet.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from app.services.utils.errors import ValidationError
from app.services.utils.logger import logger

TICK_MODEL_REAL = "real"
TICK_MODEL_GENERATED = "generated"
TICK_MODEL_TRADING_BAR = "trading_bar"
TICK_MODEL_OHLC_M1 = "ohlc_m1"

SUPPORTED_MODELS: frozenset[str] = frozenset(
    {
        TICK_MODEL_REAL,
        TICK_MODEL_GENERATED,
        TICK_MODEL_TRADING_BAR,
        TICK_MODEL_OHLC_M1,
    }
)

SPREAD_NATIVE = "native_spread"
SPREAD_FIXED = "fixed_spread"
SPREAD_VARIABLE = "variable_spread"

SUPPORTED_SPREAD_MODELS: frozenset[str] = frozenset(
    {SPREAD_NATIVE, SPREAD_FIXED, SPREAD_VARIABLE}
)

_PHASE_OPEN_CODE = np.uint8(1)
_PHASE_HIGH_CODE = np.uint8(2)
_PHASE_LOW_CODE = np.uint8(4)
_PHASE_CLOSE_CODE = np.uint8(8)

_SIGNAL_COLUMNS: tuple[str, ...] = (
    "entry_signal",
    "exit_signal",
    "pending_signal",
    "cancel_pending_signal",
    "pending_signal_2",
    "cancel_pending_signal_2",
    "price",
    "price_2",
    "sl",
    "tp",
)

_BASIC_SIGNAL_COLUMNS: tuple[str, ...] = (
    "entry_signal",
    "exit_signal",
    "pending_signal",
    "cancel_pending_signal",
    "sl",
    "tp",
)

_DATETIME_CANDIDATES: tuple[str, ...] = (
    "Datetime",
    "datetime",
    "time",
    "Time",
    "timestamp",
    "Timestamp",
)

_DEFAULT_BAR_SECONDS = 60
_TIMEFRAME_SECONDS: dict[str, int] = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
    "W1": 604800,
    "MN1": 2592000,
}

def _ensure_datetime_index(data: pd.DataFrame) -> pd.DataFrame:
    """Description.
        Return data indexed by a DatetimeIndex named ``Datetime``.
    
    Args:
        data: pd.DataFrame.
    
    Returns:
        pd.DataFrame.
    """
    logger.debug("Ensuring the generator input DataFrame has a valid DatetimeIndex.")
    if isinstance(data.index, pd.DatetimeIndex):
        return data

    for column in _DATETIME_CANDIDATES:
        if column in data.columns:
            out = data.copy()
            out.index = pd.DatetimeIndex(out[column], name="Datetime")
            return out.drop(columns=[column])

    raise ValidationError(
        "DataFrame must have a DatetimeIndex or a datetime column "
        "(Datetime, datetime, time, timestamp)."
    )


class TicksGenerator:
    """Generate standardized tick frames from real bars or ticks."""

    def __init__(
        self,
        model: str,
        trading_timeframe: str,
        *,
        m1_bars: pd.DataFrame | None = None,
        real_ticks: pd.DataFrame | None = None,
        point_value: float = 0.00001,
        spread_model: str = SPREAD_NATIVE,
        fixed_spread_points: float | None = None,
        min_spread_points: float | None = None,
        max_spread_points: float | None = None,
        random_seed: int | None = None,
    ) -> None:
        """Description.
            Initialize the generator and validate the configuration.
        
        Args:
            model: str.
            trading_timeframe: str.
            m1_bars: pd.DataFrame | None.
            real_ticks: pd.DataFrame | None.
            point_value: float.
            spread_model: str.
            fixed_spread_points: float | None.
            min_spread_points: float | None.
            max_spread_points: float | None.
            random_seed: int | None.
        
        Returns:
            None.
        """
        self.model = str(model).lower()
        self.trading_timeframe = str(trading_timeframe).upper()
        self.m1_bars = m1_bars
        self.real_ticks = real_ticks
        self.point_value = float(point_value)
        self.spread_model = str(spread_model).lower()
        self.fixed_spread_points = fixed_spread_points
        self.min_spread_points = min_spread_points
        self.max_spread_points = max_spread_points
        self._random_seed = random_seed
        self._validate_config()
        logger.debug("Initialized TicksGenerator for model=%s.", self.model)

    def _validate_config(self) -> None:
        """Description.
            Validate model, point value, and spread configuration.
        
        Args:
            None.
        
        Returns:
            None.
        """
        logger.debug(f"Validating TicksGenerator config for model={self.model}, spread_model={self.spread_model}.")
        if self.model not in SUPPORTED_MODELS:
            raise ValidationError(
                f"Unsupported ticks model: {self.model}. "
                f"Supported models: {sorted(SUPPORTED_MODELS)}"
            )
        if self.point_value <= 0.0:
            raise ValidationError("point_value must be > 0.")
        if self.spread_model not in SUPPORTED_SPREAD_MODELS:
            raise ValidationError(
                f"Unsupported spread_model: {self.spread_model}. "
                f"Supported: {sorted(SUPPORTED_SPREAD_MODELS)}"
            )
        self._validate_spread_config()

    def _validate_spread_config(self) -> None:
        """Description.
            Validate spread-model-specific point bounds.
        
        Args:
            None.
        
        Returns:
            None.
        """
        logger.debug(f"Validating spread parameters for spread_model={self.spread_model}.")
        if self.spread_model == SPREAD_FIXED:
            if self.fixed_spread_points is None:
                raise ValidationError(
                    "fixed_spread_points is required for the fixed_spread model."
                )
            if float(self.fixed_spread_points) < 0.0:
                raise ValidationError("fixed_spread_points must be >= 0.")
        if self.spread_model == SPREAD_VARIABLE:
            if self.min_spread_points is None or self.max_spread_points is None:
                raise ValidationError(
                    "min_spread_points and max_spread_points are required for "
                    "the variable_spread model."
                )
            if (
                float(self.min_spread_points) < 0.0
                or float(self.max_spread_points) < 0.0
            ):
                raise ValidationError(
                    "min_spread_points and max_spread_points must be >= 0."
                )
            if float(self.min_spread_points) > float(self.max_spread_points):
                raise ValidationError(
                    "min_spread_points cannot exceed max_spread_points."
                )

    def generate(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Description.
            Generate a standardized tick frame for the configured model.
        
        Args:
            bars: pd.DataFrame.
        
        Returns:
            pd.DataFrame.
        """
        logger.debug(
            f"Generating ticks using model='{self.model}' for "
            f"timeframe='{self.trading_timeframe}'."
        )
        if self.model == TICK_MODEL_TRADING_BAR:
            return self._four_tick_frame(bars)
        if self.model == TICK_MODEL_OHLC_M1:
            return self._ohlc_m1_frame(bars)
        if self.model == TICK_MODEL_GENERATED:
            return self._generated_frame(bars)
        return self._real_frame(bars)

    @staticmethod
    def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
        """Description.
            Return the actual column name matching any candidate.
        
        Args:
            df: pd.DataFrame.
            candidates: list[str].
        
        Returns:
            str | None.
        """
        logger.debug(f"Searching DataFrame for matching columns in: {candidates}")
        lower = {str(column).lower(): str(column) for column in df.columns}
        for name in candidates:
            if name.lower() in lower:
                return lower[name.lower()]
        return None

    @classmethod
    def _require_col(cls, df: pd.DataFrame, candidates: list[str], context: str) -> str:
        """Description.
            Return a required column name or raise.
        
        Args:
            df: pd.DataFrame.
            candidates: list[str].
            context: str.
        
        Returns:
            str.
        """
        logger.debug(f"Validating that one of the candidate columns {candidates} is present.")
        column = cls._find_col(df, candidates)
        if column is None:
            raise ValidationError(f"{context} requires one of columns: {candidates}")
        return column

    @staticmethod
    def _ensure_signal_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Description.
            Return a copy of df with all signal columns present.
        
        Args:
            df: pd.DataFrame.
        
        Returns:
            pd.DataFrame.
        """
        logger.debug("Ensuring the generated DataFrame contains standard signal fields.")
        out = df.copy()
        for column in _SIGNAL_COLUMNS:
            if column not in out.columns:
                out[column] = 0.0
        return out

    @staticmethod
    def _infer_bar_seconds(index: pd.DatetimeIndex) -> int:
        """Description.
            Infer bar duration in seconds from median index spacing.
        
        Args:
            index: pd.DatetimeIndex.
        
        Returns:
            int.
        """
        logger.debug("Inferring bar duration in seconds from the DatetimeIndex median spacing.")
        if len(index) > 1:
            deltas = index.to_series().diff().dropna()
            if not deltas.empty:
                return int(max(1, deltas.median().total_seconds()))
        return _DEFAULT_BAR_SECONDS

    def _configured_bar_seconds(self) -> int:
        """Description.
            Return the configured trading-timeframe duration in seconds.
        
        Args:
            None.
        
        Returns:
            int.
        """
        logger.debug(f"Resolving duration in seconds for configured timeframe: {self.trading_timeframe}")
        return _TIMEFRAME_SECONDS.get(self.trading_timeframe, _DEFAULT_BAR_SECONDS)

    @staticmethod
    def _four_tick_offsets_ms(bar_seconds: int) -> npt.NDArray[np.int64]:
        """Description.
            Return four within-bar millisecond offsets.
        
        Args:
            bar_seconds: int.
        
        Returns:
            npt.NDArray[np.int64].
        """
        logger.debug(f"Calculating four intra-bar millisecond offsets for bar_seconds={bar_seconds}")
        bar_ms = max(1, int(bar_seconds) * 1000)
        close_offset = max(0, bar_ms - 1)
        first_inner = max(1, bar_ms // 3)
        second_inner = max(first_inner + 1, (2 * bar_ms) // 3)
        second_inner = min(second_inner, max(first_inner + 1, close_offset - 1))
        return np.array([0, first_inner, second_inner, close_offset], dtype=np.int64)

    def _spread_points(
        self,
        native_per_tick: npt.NDArray[np.float64],
        total: int,
    ) -> npt.NDArray[np.float64]:
        """Description.
            Return per-tick spread points for the configured model.
        
        Args:
            native_per_tick: npt.NDArray[np.float64].
            total: int.
        
        Returns:
            npt.NDArray[np.float64].
        """
        logger.debug(f"Calculating tick spread points (spread_model={self.spread_model}, count={total}).")
        if self.spread_model == SPREAD_NATIVE:
            return np.maximum(native_per_tick, 0.0)
        if self.spread_model == SPREAD_FIXED:
            fixed = max(0.0, float(self.fixed_spread_points or 0.0))
            return np.full(total, fixed, dtype=np.float64)
        low = float(self.min_spread_points or 0.0)
        high = float(self.max_spread_points or 0.0)
        draws = np.random.default_rng(self._random_seed).uniform(low, high, size=total)
        return np.maximum(0.0, draws)

    def _four_tick_frame(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Description.
            Build a four-tick-per-bar frame from OHLC bars.
        
        Args:
            bars: pd.DataFrame.
        
        Returns:
            pd.DataFrame.
        """
        logger.debug(f"Building four-tick-per-bar frame for {len(bars)} bars.")
        if bars is None or bars.empty:
            return self._empty_frame(_SIGNAL_COLUMNS)

        bars = _ensure_datetime_index(bars)
        if not bars.index.is_monotonic_increasing:
            bars = bars.sort_index()
        open_col = self._require_col(bars, ["Open"], "four-tick generation")
        high_col = self._require_col(bars, ["High"], "four-tick generation")
        low_col = self._require_col(bars, ["Low"], "four-tick generation")
        close_col = self._require_col(bars, ["Close"], "four-tick generation")
        spread_col = self._find_col(bars, ["Spread"])

        n_bars = len(bars.index)

        def col_or_zeros(name: str | None) -> npt.NDArray[np.float64]:
            """Description.
                Return the named column as a NaN-free float array, or zeros.
            
            Args:
                name: str | None.
            
            Returns:
                npt.NDArray[np.float64].
            """
            logger.debug(f"Coercing column '{name}' to NaN-free float array or returning zeros.")
            if name is None:
                return np.zeros(n_bars, dtype=np.float64)
            values = pd.to_numeric(bars[name], errors="coerce").to_numpy(
                dtype=np.float64,
                copy=False,
            )
            return np.nan_to_num(values, nan=0.0)

        open_arr = col_or_zeros(open_col)
        high_arr = col_or_zeros(high_col)
        low_arr = col_or_zeros(low_col)
        close_arr = col_or_zeros(close_col)
        native_spread_arr = col_or_zeros(spread_col)
        signal_arrays = {
            column: col_or_zeros(self._find_col(bars, [column]))
            for column in _SIGNAL_COLUMNS
        }

        bar_seconds = (
            self._infer_bar_seconds(bars.index)
            if n_bars > 1
            else self._configured_bar_seconds()
        )
        offsets_ms = self._four_tick_offsets_ms(bar_seconds)

        bullish = close_arr >= open_arr
        total = n_bars * 4
        bid: npt.NDArray[np.float64] = np.empty(total, dtype=np.float64)
        bid[0::4] = open_arr
        bid[1::4] = np.where(bullish, low_arr, high_arr)
        bid[2::4] = np.where(bullish, high_arr, low_arr)
        bid[3::4] = close_arr

        phases: npt.NDArray[np.uint8] = np.empty(total, dtype=np.uint8)
        phases[0::4] = _PHASE_OPEN_CODE
        phases[1::4] = np.where(bullish, _PHASE_LOW_CODE, _PHASE_HIGH_CODE)
        phases[2::4] = np.where(bullish, _PHASE_HIGH_CODE, _PHASE_LOW_CODE)
        phases[3::4] = _PHASE_CLOSE_CODE

        spread_points = self._spread_points(np.repeat(native_spread_arr, 4), total)
        frame: dict[str, Any] = {
            "bid": bid,
            "ask": bid + (spread_points * self.point_value),
            "last": bid,
            "spread": np.rint(np.maximum(spread_points, 0.0)).astype(np.int64),
        }
        for column, values in signal_arrays.items():
            placed: npt.NDArray[np.float64] = np.zeros(total, dtype=np.float64)
            placed[0::4] = values
            frame[column] = placed

        repeated_index = bars.index.repeat(4)
        tick_offsets = pd.to_timedelta(
            np.tile(offsets_ms.astype(np.int64), n_bars),
            unit="ms",
        )
        index = pd.DatetimeIndex(repeated_index + tick_offsets, name="Datetime")
        frame["tick_index_in_bar"] = np.tile(np.array([0, 1, 2, 3]), n_bars)
        frame["is_bar_close"] = phases

        result = pd.DataFrame(frame, index=index, copy=False)
        result["source_bar_time"] = repeated_index
        # Four within-bar offsets are strictly increasing and bounded below one
        # bar, so with sorted input the result is already monotonic. Avoid
        # re-sorting the full output frame; guard keeps correctness regardless.
        if not result.index.is_monotonic_increasing:
            return result.sort_index()
        return result

    def _ohlc_m1_frame(self, trading_bars: pd.DataFrame) -> pd.DataFrame:
        """Description.
            Build a four-tick frame from M1 bars with merged signals.
        
        Args:
            trading_bars: pd.DataFrame.
        
        Returns:
            pd.DataFrame.
        """
        logger.debug(f"Building OHLC M1 tick frame for {len(trading_bars)} trading bars.")
        if self.m1_bars is None or self.m1_bars.empty:
            raise ValidationError("TICK_MODEL_OHLC_M1 requires non-empty m1_bars.")
        m1_with_signals = self._merge_signals_onto(self.m1_bars, trading_bars)
        return self._four_tick_frame(m1_with_signals)

    def _merge_signals_onto(
        self,
        target: pd.DataFrame,
        signal_bars: pd.DataFrame,
    ) -> pd.DataFrame:
        """Description.
            Broadcast trading-timeframe signals onto finer-grained bars.
        
        Args:
            target: pd.DataFrame.
            signal_bars: pd.DataFrame.
        
        Returns:
            pd.DataFrame.
        """
        target_frame = _ensure_datetime_index(target.copy())
        signals = self._ensure_signal_columns(_ensure_datetime_index(signal_bars))

        tf_seconds = self._infer_bar_seconds(signals.index)
        floor = f"{max(1, tf_seconds)}s"
        tf_signals = signals[list(_SIGNAL_COLUMNS)].copy()
        tf_signals.index = tf_signals.index.floor(floor)

        mapped = tf_signals.reindex(target_frame.index.floor(floor)).fillna(0.0)
        mapped.index = target_frame.index
        for column in _SIGNAL_COLUMNS:
            target_frame[column] = mapped[column]

        logger.debug("Merged trading signals onto {} bars.", len(target_frame))
        return target_frame

    def _generated_frame(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Description.
            Interpolate each trading-timeframe bar into tick-volume ticks.
        
        Args:
            bars: pd.DataFrame.
        
        Returns:
            pd.DataFrame.
        """
        logger.debug(f"Interpolating {len(bars)} bars into tick-volume generated ticks.")
        if bars is None or bars.empty:
            return self._empty_frame(_BASIC_SIGNAL_COLUMNS)

        frame = _ensure_datetime_index(bars)
        # Sort the (small) input bars once so generated ticks come out already
        # ordered. This lets us skip a full sort of the (huge) output frame,
        # which otherwise duplicates every tick column and dominates runtime /
        # peak memory on large inputs.
        if not frame.index.is_monotonic_increasing:
            frame = frame.sort_index()
        open_col = self._require_col(frame, ["Open"], TICK_MODEL_GENERATED)
        high_col = self._require_col(frame, ["High"], TICK_MODEL_GENERATED)
        low_col = self._require_col(frame, ["Low"], TICK_MODEL_GENERATED)
        close_col = self._require_col(frame, ["Close"], TICK_MODEL_GENERATED)
        volume_col = self._require_col(
            frame,
            ["tick_volume", "Volume", "volume"],
            TICK_MODEL_GENERATED,
        )
        spread_col = self._find_col(frame, ["Spread"])

        def bar_floats(name: str) -> npt.NDArray[np.float64]:
            """Description.
                Return the named bar column as a NaN-free float array.
            
            Args:
                name: str.
            
            Returns:
                npt.NDArray[np.float64].
            """
            logger.debug(f"Extracting field '{name}' as native float array.")
            values = pd.to_numeric(frame[name], errors="coerce").to_numpy(
                dtype=np.float64,
                copy=False,
            )
            return np.nan_to_num(values, nan=0.0)

        open_b = bar_floats(open_col)
        high_b = bar_floats(high_col)
        low_b = bar_floats(low_col)
        close_b = bar_floats(close_col)
        native_b = (
            bar_floats(spread_col)
            if spread_col is not None
            else np.zeros(len(open_b), dtype=np.float64)
        )
        vol_b = np.maximum(4, bar_floats(volume_col).astype(np.int64))
        total = int(vol_b.sum())
        if total == 0:
            return self._empty_frame(_BASIC_SIGNAL_COLUMNS)

        price, local_i, vol_rep = self._interpolate_generated(
            open_b,
            high_b,
            low_b,
            close_b,
            vol_b,
            total,
        )
        spread_points = self._spread_points(np.repeat(native_b, vol_b), total)
        phases = self._generated_phase_codes(open_b, close_b, vol_b, local_i, vol_rep)

        n_bars = len(vol_b)
        bar_seconds = (
            self._infer_bar_seconds(frame.index)
            if n_bars > 1
            else self._configured_bar_seconds()
        )
        offset_ms = (max(1, bar_seconds * 1000) * local_i) // np.maximum(vol_rep, 1)
        repeated_index = frame.index.repeat(vol_b)
        index = pd.DatetimeIndex(
            repeated_index + pd.to_timedelta(offset_ms, unit="ms"),
            name="Datetime",
        )

        data: dict[str, Any] = {
            "bid": price,
            "ask": price + spread_points * self.point_value,
            "last": price,
            "spread": np.rint(np.maximum(spread_points, 0.0)).astype(np.int64),
        }
        open_offsets = np.cumsum(vol_b) - vol_b
        for column in _BASIC_SIGNAL_COLUMNS:
            signal_col = self._find_col(frame, [column])
            values = np.zeros(total, dtype=np.float64)
            if signal_col is not None:
                values[open_offsets] = bar_floats(signal_col)
            data[column] = values
        data["tick_index_in_bar"] = local_i
        data["is_bar_close"] = phases

        result = pd.DataFrame(data, index=index, copy=False)
        result["source_bar_time"] = repeated_index
        # Within-bar offsets are strictly increasing and bounded below one bar,
        # so with sorted input the result is already monotonic. The guard keeps
        # correctness if that ever fails to hold.
        if not result.index.is_monotonic_increasing:
            return result.sort_index()
        return result

    @staticmethod
    def _interpolate_generated(
        open_b: npt.NDArray[np.float64],
        high_b: npt.NDArray[np.float64],
        low_b: npt.NDArray[np.float64],
        close_b: npt.NDArray[np.float64],
        vol_b: npt.NDArray[np.int64],
        total: int,
    ) -> tuple[
        npt.NDArray[np.float64],
        npt.NDArray[np.int64],
        npt.NDArray[np.int64],
    ]:
        """Description.
            Vectorize piecewise-linear OHLC interpolation across bars.
        
        Args:
            open_b: npt.NDArray[np.float64].
            high_b: npt.NDArray[np.float64].
            low_b: npt.NDArray[np.float64].
            close_b: npt.NDArray[np.float64].
            vol_b: npt.NDArray[np.int64].
            total: int.
        
        Returns:
            tuple[npt.NDArray[np.float64], npt.NDArray[np.int64], npt.NDArray[np.int64]].
        """
        logger.debug(f"Interpolating OHLC values vectorially (total output ticks: {total}).")
        bar_start: npt.NDArray[np.int64] = np.repeat(
            np.cumsum(vol_b) - vol_b,
            vol_b,
        )
        local_i = np.arange(total) - bar_start
        vol_rep: npt.NDArray[np.int64] = np.repeat(vol_b, vol_b)

        steps = vol_b - 1
        base = steps // 3
        rem = steps % 3
        seg0 = base + (rem > 0)
        seg1 = base + (rem > 1)
        b1: npt.NDArray[np.int64] = np.repeat(seg0, vol_b)
        b2: npt.NDArray[np.int64] = np.repeat(seg0 + seg1, vol_b)
        seg0_rep: npt.NDArray[np.int64] = np.repeat(
            np.maximum(seg0, 1),
            vol_b,
        )
        seg1_rep: npt.NDArray[np.int64] = np.repeat(
            np.maximum(seg1, 1),
            vol_b,
        )
        seg2_rep: npt.NDArray[np.int64] = np.repeat(
            np.maximum(base, 1),
            vol_b,
        )

        bullish = close_b >= open_b
        w0: npt.NDArray[np.float64] = np.repeat(open_b, vol_b)
        w3: npt.NDArray[np.float64] = np.repeat(close_b, vol_b)
        w1: npt.NDArray[np.float64] = np.repeat(
            np.where(bullish, low_b, high_b),
            vol_b,
        )
        w2: npt.NDArray[np.float64] = np.repeat(
            np.where(bullish, high_b, low_b),
            vol_b,
        )

        in_seg0 = local_i <= b1
        in_seg1 = (local_i > b1) & (local_i <= b2)
        price: npt.NDArray[np.float64] = np.where(
            in_seg0,
            w0 + (w1 - w0) * (local_i / seg0_rep),
            np.where(
                in_seg1,
                w1 + (w2 - w1) * ((local_i - b1) / seg1_rep),
                w2 + (w3 - w2) * ((local_i - b2) / seg2_rep),
            ),
        )
        return price, local_i, vol_rep

    @staticmethod
    def _generated_phase_codes(
        open_b: npt.NDArray[np.float64],
        close_b: npt.NDArray[np.float64],
        vol_b: npt.NDArray[np.int64],
        local_i: npt.NDArray[np.int64],
        vol_rep: npt.NDArray[np.int64],
    ) -> npt.NDArray[np.uint8]:
        """Description.
            Return generated tick phase bitmasks without scanning output prices.
        
        Args:
            open_b: npt.NDArray[np.float64].
            close_b: npt.NDArray[np.float64].
            vol_b: npt.NDArray[np.int64].
            local_i: npt.NDArray[np.int64].
            vol_rep: npt.NDArray[np.int64].
        
        Returns:
            npt.NDArray[np.uint8].
        """
        logger.debug(f"Calculating generated tick phase bitmasks (total ticks: {local_i.shape[0]}).")
        steps = vol_b - 1
        base = steps // 3
        rem = steps % 3
        seg0 = base + (rem > 0)
        seg1 = base + (rem > 1)
        first_turn: npt.NDArray[np.int64] = np.repeat(seg0, vol_b)
        second_turn: npt.NDArray[np.int64] = np.repeat(seg0 + seg1, vol_b)
        bullish: npt.NDArray[np.bool_] = np.repeat(close_b >= open_b, vol_b)
        high_i = np.where(bullish, second_turn, first_turn)
        low_i = np.where(bullish, first_turn, second_turn)

        bitmask = np.zeros(local_i.shape[0], dtype=np.uint8)
        bitmask[local_i == 0] |= _PHASE_OPEN_CODE
        bitmask[local_i == high_i] |= _PHASE_HIGH_CODE
        bitmask[local_i == low_i] |= _PHASE_LOW_CODE
        bitmask[local_i == (vol_rep - 1)] |= _PHASE_CLOSE_CODE
        return bitmask

    def _real_frame(self, trading_bars: pd.DataFrame) -> pd.DataFrame:
        """Description.
            Standardize real ticks and attach merged trading signals.
        
        Args:
            trading_bars: pd.DataFrame.
        
        Returns:
            pd.DataFrame.
        """
        logger.debug(
            f"Merging real ticks ({len(self.real_ticks)}) with trading "
            f"signals ({len(trading_bars)})."
        )
        if self.real_ticks is None or self.real_ticks.empty:
            raise ValidationError("TICK_MODEL_REAL requires non-empty real_ticks.")

        ticks = _ensure_datetime_index(self.real_ticks.copy())
        signals = self._ensure_signal_columns(_ensure_datetime_index(trading_bars))
        bid_col = self._require_col(ticks, ["bid"], TICK_MODEL_REAL)
        ask_col = self._require_col(ticks, ["ask"], TICK_MODEL_REAL)
        last_col = self._find_col(ticks, ["last"])
        spread_col = self._find_col(ticks, ["spread"])

        tf_seconds = self._infer_bar_seconds(signals.index)
        floor = f"{max(1, tf_seconds)}s"
        bucket = ticks.index.floor(floor)
        first_in_bucket = ~bucket.duplicated()
        tf_signal = signals[list(_BASIC_SIGNAL_COLUMNS)].copy()
        tf_signal.index = tf_signal.index.floor(floor)
        merged = tf_signal.reindex(bucket).fillna(0.0).reset_index(drop=True)

        out = pd.DataFrame(index=ticks.index)
        out["bid"] = ticks[bid_col].astype(float)
        out["ask"] = ticks[ask_col].astype(float)
        out["last"] = (
            ticks[last_col].astype(float) if last_col is not None else out["bid"]
        )
        out["spread"] = (
            ticks[spread_col].astype(float)
            if spread_col is not None
            else (out["ask"] - out["bid"]) / self.point_value
        )

        for column in _BASIC_SIGNAL_COLUMNS:
            out[column] = merged[column].to_numpy()
            out.loc[~first_in_bucket, column] = 0.0

        out["source_bar_time"] = bucket
        out["tick_index_in_bar"] = (
            pd.Series(bucket, index=out.index).groupby(bucket).cumcount()
        )
        out["is_bar_close"] = self._real_phase_labels(bucket, out["bid"])
        out.index = pd.DatetimeIndex(out.index, name="Datetime")
        return out.sort_index()

    @staticmethod
    def _real_phase_labels(
        bucket: pd.DatetimeIndex,
        bids: pd.Series,
    ) -> npt.NDArray[np.uint8]:
        """Description.
            Return open/high/low/close phase bitmasks within each bucket.
        
        Args:
            bucket: pd.DatetimeIndex.
            bids: pd.Series.
        
        Returns:
            npt.NDArray[np.uint8].
        """
        logger.debug(
            f"Labeling open/high/low/close phase bitmasks within each "
            f"time bucket (total: {len(bids)})."
        )
        total = len(bids)
        bucket_arr = np.asarray(bucket)
        bid_series = pd.Series(bids.to_numpy(dtype=np.float64, copy=False))
        pos_series = pd.Series(np.arange(total))
        open_idx = pos_series.groupby(bucket_arr, sort=False).first().to_numpy()
        close_idx = pos_series.groupby(bucket_arr, sort=False).last().to_numpy()
        high_idx = bid_series.groupby(bucket_arr, sort=False).idxmax().to_numpy()
        low_idx = bid_series.groupby(bucket_arr, sort=False).idxmin().to_numpy()

        is_open: npt.NDArray[np.bool_] = np.zeros(total, dtype=bool)
        is_close: npt.NDArray[np.bool_] = np.zeros(total, dtype=bool)
        is_high: npt.NDArray[np.bool_] = np.zeros(total, dtype=bool)
        is_low: npt.NDArray[np.bool_] = np.zeros(total, dtype=bool)
        is_open[open_idx] = True
        is_close[close_idx] = True
        is_high[high_idx] = True
        is_low[low_idx] = True
        bitmask: npt.NDArray[np.uint8] = np.zeros(total, dtype=np.uint8)
        bitmask[is_open] |= _PHASE_OPEN_CODE
        bitmask[is_high] |= _PHASE_HIGH_CODE
        bitmask[is_low] |= _PHASE_LOW_CODE
        bitmask[is_close] |= _PHASE_CLOSE_CODE
        return bitmask

    @staticmethod
    def _empty_frame(signal_columns: tuple[str, ...]) -> pd.DataFrame:
        """Description.
            Return an empty tick frame with the standard column layout.
        
        Args:
            signal_columns: tuple[str, ...].
        
        Returns:
            pd.DataFrame.
        """
        logger.debug(f"Constructing empty tick DataFrame structure with signals: {signal_columns}")
        columns = [
            "bid",
            "ask",
            "last",
            "spread",
            *signal_columns,
            "source_bar_time",
            "tick_index_in_bar",
            "is_bar_close",
        ]
        return pd.DataFrame(columns=columns)


def _to_dataframe(
    data: pd.DataFrame | list[dict[str, Any]] | None,
) -> pd.DataFrame | None:
    """Description.
        Coerce list-of-records input into a DataFrame.
    
    Args:
        data: pd.DataFrame | list[dict[str, Any]] | None.
    
    Returns:
        pd.DataFrame | None.
    """
    logger.debug("Coercing records input into pandas DataFrame structure.")
    if data is None:
        return None
    if isinstance(data, pd.DataFrame):
        return data
    return pd.DataFrame(data)


def generate_ticks(
    *,
    model: str,
    trading_timeframe: str,
    bars: pd.DataFrame | list[dict[str, Any]] | None = None,
    m1_bars: pd.DataFrame | list[dict[str, Any]] | None = None,
    real_ticks: pd.DataFrame | list[dict[str, Any]] | None = None,
    point_value: float = 0.00001,
    spread_model: str = SPREAD_NATIVE,
    fixed_spread_points: float | None = None,
    min_spread_points: float | None = None,
    max_spread_points: float | None = None,
    random_seed: int | None = None,
    request_id: str | None = None,
) -> pd.DataFrame:
    """Description.
        Generate standardized ticks as a columnar DataFrame.
    
    Args:
        model: str.
        trading_timeframe: str.
        bars: pd.DataFrame | list[dict[str, Any]] | None.
        m1_bars: pd.DataFrame | list[dict[str, Any]] | None.
        real_ticks: pd.DataFrame | list[dict[str, Any]] | None.
        point_value: float.
        spread_model: str.
        fixed_spread_points: float | None.
        min_spread_points: float | None.
        max_spread_points: float | None.
        random_seed: int | None.
        request_id: str | None.
    
    Returns:
        pd.DataFrame.
    """
    logger.info(
        "Generating tick frame model={} timeframe={} | request_id={}",
        model,
        trading_timeframe,
        request_id,
    )
    generator = TicksGenerator(
        model=model,
        trading_timeframe=trading_timeframe,
        m1_bars=_to_dataframe(m1_bars),
        real_ticks=_to_dataframe(real_ticks),
        point_value=point_value,
        spread_model=spread_model,
        fixed_spread_points=fixed_spread_points,
        min_spread_points=min_spread_points,
        max_spread_points=max_spread_points,
        random_seed=random_seed,
    )
    signal_bars = _to_dataframe(bars)
    if signal_bars is None:
        signal_bars = pd.DataFrame()
    raw = generator.generate(signal_bars)
    if raw.empty:
        return pd.DataFrame(columns=["timestamp", *raw.columns.tolist()])
    raw.insert(0, "timestamp", raw.index)
    raw.index = pd.RangeIndex(len(raw))
    return raw


def _chunk_bounds(n_rows: int, size: int) -> list[tuple[int, int]]:
    """Description.
        Return row ranges covering n_rows in size chunks.
    
    Args:
        n_rows: int.
        size: int.
    
    Returns:
        list[tuple[int, int]].
    """
    logger.debug(f"Calculating basic chunk bounds for {n_rows} rows (chunk size: {size}).")
    step = max(1, size)
    return [(index, min(index + step, n_rows)) for index in range(0, n_rows, step)]


def _find_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    """Description.
        Return the first matching column name case-insensitively.
    
    Args:
        df: pd.DataFrame.
        candidates: tuple[str, ...].
    
    Returns:
        str | None.
    """
    logger.debug(f"Searching DataFrame for matching columns in: {candidates}")
    lower = {str(column).lower(): str(column) for column in df.columns}
    for name in candidates:
        if name.lower() in lower:
            return lower[name.lower()]
    return None


def _estimated_generated_counts(source: pd.DataFrame) -> npt.NDArray[np.int64]:
    """Description.
        Return estimated generated output rows per input bar.
    
    Args:
        source: pd.DataFrame.
    
    Returns:
        npt.NDArray[np.int64].
    """
    logger.debug(f"Estimating generated output rows per input bar for DataFrame with {len(source)} rows.")
    volume_col = _find_column(source, ("tick_volume", "Volume", "volume"))
    if volume_col is None:
        raise ValidationError(
            "generated chunking requires one of columns: tick_volume, Volume, volume"
        )
    values = pd.to_numeric(source[volume_col], errors="coerce").to_numpy(
        dtype=np.float64,
        copy=False,
    )
    return np.maximum(4, np.nan_to_num(values, nan=0.0).astype(np.int64))


def _output_aware_chunk_bounds(
    counts: npt.NDArray[np.int64],
    max_output_rows: int,
) -> list[tuple[int, int]]:
    """Description.
        Return input row ranges targeting a maximum generated output size.
    
    Args:
        counts: npt.NDArray[np.int64].
        max_output_rows: int.
    
    Returns:
        list[tuple[int, int]].
    """
    logger.debug(f"Calculating output-aware chunk bounds targeting max output rows: {max_output_rows}")
    if len(counts) == 0:
        return []

    target = max(1, int(max_output_rows))
    bounds: list[tuple[int, int]] = []
    start = 0
    running = 0
    for index, count in enumerate(counts):
        estimated = max(1, int(count))
        if index > start and running + estimated > target:
            bounds.append((start, index))
            start = index
            running = 0
        running += estimated
    bounds.append((start, len(counts)))
    return bounds


_InputChunk = tuple[pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None]


def _parquet_input_chunks(
    model: str,
    bars_df: pd.DataFrame | None,
    m1_df: pd.DataFrame | None,
    real_df: pd.DataFrame | None,
    chunk_size: int,
    max_output_rows_per_chunk: int,
) -> Iterator[_InputChunk]:
    """Description.
        Yield input slices per chunk by model.
    
    Args:
        model: str.
        bars_df: pd.DataFrame | None.
        m1_df: pd.DataFrame | None.
        real_df: pd.DataFrame | None.
        chunk_size: int.
        max_output_rows_per_chunk: int.
    
    Returns:
        Iterator[_InputChunk].
    """
    logger.debug(f"Segmenting parquet input datasets into chunks for ticks model={model}.")
    if model == TICK_MODEL_REAL:
        yield bars_df, m1_df, real_df
        return

    source = m1_df if model == TICK_MODEL_OHLC_M1 else bars_df
    if source is None or source.empty:
        yield bars_df, m1_df, real_df
        return

    if model == TICK_MODEL_GENERATED:
        bounds = _output_aware_chunk_bounds(
            _estimated_generated_counts(source),
            max_output_rows_per_chunk,
        )
    elif model in {TICK_MODEL_TRADING_BAR, TICK_MODEL_OHLC_M1}:
        rows_per_chunk = max(1, int(max_output_rows_per_chunk) // 4)
        bounds = _chunk_bounds(len(source), min(chunk_size, rows_per_chunk))
    else:
        bounds = _chunk_bounds(len(source), chunk_size)

    for start, stop in bounds:
        piece = source.iloc[start:stop]
        if model == TICK_MODEL_OHLC_M1:
            yield bars_df, piece, real_df
        else:
            yield piece, m1_df, real_df


def generate_ticks_to_parquet(
    *,
    model: str,
    trading_timeframe: str,
    path: str | Path,
    bars: pd.DataFrame | list[dict[str, Any]] | None = None,
    m1_bars: pd.DataFrame | list[dict[str, Any]] | None = None,
    real_ticks: pd.DataFrame | list[dict[str, Any]] | None = None,
    point_value: float = 0.00001,
    spread_model: str = SPREAD_NATIVE,
    fixed_spread_points: float | None = None,
    min_spread_points: float | None = None,
    max_spread_points: float | None = None,
    random_seed: int | None = None,
    chunk_size: int = 100_000,
    max_output_rows_per_chunk: int = 2_000_000,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Stream generated ticks to a Parquet file with bounded memory.
    
    Args:
        model: str.
        trading_timeframe: str.
        path: str | Path.
        bars: pd.DataFrame | list[dict[str, Any]] | None.
        m1_bars: pd.DataFrame | list[dict[str, Any]] | None.
        real_ticks: pd.DataFrame | list[dict[str, Any]] | None.
        point_value: float.
        spread_model: str.
        fixed_spread_points: float | None.
        min_spread_points: float | None.
        max_spread_points: float | None.
        random_seed: int | None.
        chunk_size: int.
        max_output_rows_per_chunk: int.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Writing ticks to parquet model={} path={} | request_id={}",
        model,
        out_path,
        request_id,
    )

    bars_df = _to_dataframe(bars)
    m1_df = _to_dataframe(m1_bars)
    real_df = _to_dataframe(real_ticks)

    writer: pq.ParquetWriter | None = None
    rows = 0
    columns: list[str] = []
    last_frame: pd.DataFrame | None = None
    try:
        for chunk_bars, chunk_m1, chunk_real in _parquet_input_chunks(
            model,
            bars_df,
            m1_df,
            real_df,
            chunk_size,
            max_output_rows_per_chunk,
        ):
            frame = generate_ticks(
                model=model,
                trading_timeframe=trading_timeframe,
                bars=chunk_bars,
                m1_bars=chunk_m1,
                real_ticks=chunk_real,
                point_value=point_value,
                spread_model=spread_model,
                fixed_spread_points=fixed_spread_points,
                min_spread_points=min_spread_points,
                max_spread_points=max_spread_points,
                random_seed=random_seed,
                request_id=request_id,
            )
            last_frame = frame
            if frame.empty:
                continue
            table = pa.Table.from_pandas(frame, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(out_path, table.schema)
                columns = [str(column) for column in frame.columns]
            writer.write_table(table)
            rows += len(frame)
    finally:
        if writer is not None:
            writer.close()

    if writer is None and last_frame is not None:
        last_frame.to_parquet(out_path, index=False)
        columns = [str(column) for column in last_frame.columns]

    return {"path": str(out_path), "rows": rows, "columns": columns}


__all__ = [
    "SPREAD_FIXED",
    "SPREAD_NATIVE",
    "SPREAD_VARIABLE",
    "SUPPORTED_MODELS",
    "SUPPORTED_SPREAD_MODELS",
    "TICK_MODEL_GENERATED",
    "TICK_MODEL_OHLC_M1",
    "TICK_MODEL_REAL",
    "TICK_MODEL_TRADING_BAR",
    "TicksGenerator",
    "generate_ticks",
    "generate_ticks_to_parquet",
]
