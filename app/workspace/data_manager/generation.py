"""Vectorized batch tick generation and Parquet streaming.

Description:
    Provides vectorized generation producing standardized tick DataFrames from
    historical bars or ticks (TicksGenerator, generate_ticks), supporting
    multiple tick models and spread models, with streaming Parquet persistence
    (generate_ticks_to_parquet).

Purpose:
    FEAT-DATAMGR-GENERATION: Vectorized batch tick generation and streaming.

Key Capabilities:
    - FR-DATAMGR-GENERATION-PHASE-OPEN: Numeric phase code for bar Open tick.
      Associated: `PHASE_OPEN_CODE`.
      Logging: Constant numerical code.
    - FR-DATAMGR-GENERATION-PHASE-HIGH: Numeric phase code for bar High tick.
      Associated: `PHASE_HIGH_CODE`.
      Logging: Constant numerical code.
    - FR-DATAMGR-GENERATION-PHASE-LOW: Numeric phase code for bar Low tick.
      Associated: `PHASE_LOW_CODE`.
      Logging: Constant numerical code.
    - FR-DATAMGR-GENERATION-PHASE-CLOSE: Numeric phase code for bar Close tick.
      Associated: `PHASE_CLOSE_CODE`.
      Logging: Constant numerical code.
    - FR-DATAMGR-GENERATION-SPREAD-FIXED: Fixed spread model identifier.
      Associated: `SPREAD_FIXED`.
      Logging: Constant string identifier.
    - FR-DATAMGR-GENERATION-SPREAD-NATIVE: Native recorded spread model identifier.
      Associated: `SPREAD_NATIVE`.
      Logging: Constant string identifier.
    - FR-DATAMGR-GENERATION-SPREAD-VARIABLE: Deterministic variable spread model.
      Associated: `SPREAD_VARIABLE`.
      Logging: Constant string identifier.
    - FR-DATAMGR-GENERATION-SUPPORTED-SPREAD-MODELS: Qualified spread model codes.
      Associated: `SUPPORTED_SPREAD_MODELS`.
      Logging: Constant configuration set.
    - FR-DATAMGR-GENERATION-SUPPORTED-TICK-MODELS: Set of qualified tick model codes.
      Associated: `SUPPORTED_TICK_MODELS`.
      Logging: Constant configuration set.
    - FR-DATAMGR-GENERATION-TICK-MODEL-GENERATED: Four-phase synthetic tick model.
      Associated: `TICK_MODEL_GENERATED`.
      Logging: Constant string identifier.
    - FR-DATAMGR-GENERATION-TICK-MODEL-OHLC-M1: 1-minute OHLC tick generation model.
      Associated: `TICK_MODEL_OHLC_M1`.
      Logging: Constant string identifier.
    - FR-DATAMGR-GENERATION-TICK-MODEL-REAL: Pass-through native real tick model code.
      Associated: `TICK_MODEL_REAL`.
      Logging: Constant string identifier.
    - FR-DATAMGR-GENERATION-TICK-MODEL-TRADING-BAR: Trading bar tick model code.
      Associated: `TICK_MODEL_TRADING_BAR`.
      Logging: Constant string identifier.
    - FR-DATAMGR-GENERATION-TICKS-GENERATOR: Vectorized batch tick generation engine.
      Associated: `TicksGenerator`.
      Logging: DEBUG tick batch generation lifecycle.
    - FR-DATAMGR-GENERATION-GENERATE-TICKS: Vectorized batch tick generation.
      Associated: `generate_ticks()`.
      Logging: DEBUG tick batch generation parameters and row counts.
    - FR-DATAMGR-GENERATION-GENERATE-TICKS-TO-PARQUET: Stream ticks to Parquet.
      Associated: `generate_ticks_to_parquet()`.
      Logging: DEBUG Parquet file streaming lifecycle and chunk counts.

Python API Usage:
    ```python
    from app.workspace.data_manager.generation import (
        TICK_MODEL_OHLC_M1,
        TicksGenerator,
        generate_ticks,
    )
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.generation
    ```
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
import pyarrow as pa
import pyarrow.parquet as pq
from app.host.logging import get_logger
from app.services.libs.enums import TIMEFRAME_SECONDS, Timeframe
from app.services.libs.generators import RandomGenerator

__all__ = [
    "PHASE_CLOSE_CODE",
    "PHASE_HIGH_CODE",
    "PHASE_LOW_CODE",
    "PHASE_OPEN_CODE",
    "SPREAD_FIXED",
    "SPREAD_NATIVE",
    "SPREAD_VARIABLE",
    "SUPPORTED_SPREAD_MODELS",
    "SUPPORTED_TICK_MODELS",
    "TICK_MODEL_GENERATED",
    "TICK_MODEL_OHLC_M1",
    "TICK_MODEL_REAL",
    "TICK_MODEL_TRADING_BAR",
    "TicksGenerator",
    "generate_ticks",
    "generate_ticks_to_parquet",
]

logger = get_logger(__name__)

# ============================================================================
# Component 2: Vectorized Batch Tick Generator & Parquet Streamer
# ============================================================================

TICK_MODEL_REAL = "real"
TICK_MODEL_GENERATED = "generated"
TICK_MODEL_TRADING_BAR = "trading_bar"
TICK_MODEL_OHLC_M1 = "ohlc_m1"

SUPPORTED_TICK_MODELS: frozenset[str] = frozenset(
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
    {
        SPREAD_NATIVE,
        SPREAD_FIXED,
        SPREAD_VARIABLE,
    }
)

PHASE_OPEN_CODE = np.uint8(1)
PHASE_HIGH_CODE = np.uint8(2)
PHASE_LOW_CODE = np.uint8(4)
PHASE_CLOSE_CODE = np.uint8(8)

_DATETIME_CANDIDATES: tuple[str, ...] = (
    "Datetime",
    "datetime",
    "time",
    "Time",
    "timestamp",
    "Timestamp",
)

_DEFAULT_BAR_SECONDS = 60


def _ensure_datetime_index(data: pd.DataFrame) -> pd.DataFrame:
    """Ensure DataFrame is indexed by a DatetimeIndex named Datetime."""
    if isinstance(data.index, pd.DatetimeIndex):
        if data.index.name != "Datetime":
            out = data.copy()
            out.index.name = "Datetime"
            return out
        return data

    for col in _DATETIME_CANDIDATES:
        if col in data.columns:
            out = data.copy()
            out.index = pd.DatetimeIndex(out[col], name="Datetime")
            return out.drop(columns=[col])

    raise ValueError(
        "DataFrame must have a DatetimeIndex or datetime column "
        "(Datetime, datetime, time, timestamp)."
    )


class TicksGenerator:
    """Vectorized generator producing standardized tick frames from bars or ticks.

    Completely decoupled from strategy signals, producing pure market data frames:
    ["bid", "ask", "last", "spread", "source_bar_time", "tick_index_in_bar",
     "is_bar_close"].
    """

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
        """Initialize generator and validate configuration."""
        self.model = model.lower()
        self.trading_timeframe = trading_timeframe.upper()
        self.m1_bars = m1_bars
        self.real_ticks = real_ticks
        self.point_value = float(point_value)
        self.spread_model = spread_model.lower()
        self.fixed_spread_points = fixed_spread_points
        self.min_spread_points = min_spread_points
        self.max_spread_points = max_spread_points
        self._random_seed = random_seed
        self._validate_config()
        logger.debug(
            "FR-DATA-BATCH-TICK-GENERATOR: initialized TicksGenerator model=%s",
            self.model,
        )

    def _validate_config(self) -> None:
        """Validate model, point value, and spread configuration."""
        if self.model not in SUPPORTED_TICK_MODELS:
            raise ValueError(
                f"Unsupported ticks model: {self.model}. "
                f"Supported models: {sorted(SUPPORTED_TICK_MODELS)}"
            )
        if self.point_value <= 0.0:
            raise ValueError("point_value must be > 0.")
        if self.spread_model not in SUPPORTED_SPREAD_MODELS:
            raise ValueError(
                f"Unsupported spread_model: {self.spread_model}. "
                f"Supported: {sorted(SUPPORTED_SPREAD_MODELS)}"
            )
        self._validate_spread_config()

    def _validate_spread_config(self) -> None:
        """Validate spread parameters for fixed and variable spread models."""
        if self.spread_model == SPREAD_FIXED:
            if self.fixed_spread_points is None:
                raise ValueError(
                    "fixed_spread_points is required for the fixed_spread model."
                )
            if float(self.fixed_spread_points) < 0.0:
                raise ValueError("fixed_spread_points must be >= 0.")
        elif self.spread_model == SPREAD_VARIABLE:
            if self.min_spread_points is None or self.max_spread_points is None:
                raise ValueError(
                    "min_spread_points and max_spread_points are required for "
                    "variable_spread model."
                )
            if (
                float(self.min_spread_points) < 0.0
                or float(self.max_spread_points) < 0.0
            ):
                raise ValueError(
                    "min_spread_points and max_spread_points must be >= 0."
                )
            if float(self.min_spread_points) > float(self.max_spread_points):
                raise ValueError("min_spread_points cannot exceed max_spread_points.")

    def generate(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Generate a standardized tick frame for the configured model."""
        logger.debug(
            "FR-DATA-BATCH-TICK-GENERATOR: generating ticks using model='%s' "
            "for timeframe='%s'.",
            self.model,
            self.trading_timeframe,
        )
        if self.model == TICK_MODEL_TRADING_BAR:
            return self._four_tick_frame(bars)
        if self.model == TICK_MODEL_OHLC_M1:
            return self._ohlc_m1_frame(bars)
        if self.model == TICK_MODEL_GENERATED:
            return self._generated_frame(bars)
        return self._real_frame(bars)

    @staticmethod
    def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
        """Return the actual column name matching any candidate case-insensitively."""
        lower = {str(col).lower(): str(col) for col in df.columns}
        for name in candidates:
            if name.lower() in lower:
                return lower[name.lower()]
        return None

    _find_col = find_col

    @classmethod
    def _require_col(cls, df: pd.DataFrame, candidates: list[str], context: str) -> str:
        """Return a required column name or raise ValueError."""
        col = cls.find_col(df, candidates)
        if col is None:
            raise ValueError(f"{context} requires one of columns: {candidates}")
        return col

    @staticmethod
    def _infer_bar_seconds(index: pd.DatetimeIndex) -> int:
        """Infer bar duration in seconds from median index spacing."""
        if len(index) > 1:
            deltas = index.to_series().diff().dropna()
            if not deltas.empty:
                return int(max(1, float(deltas.median().total_seconds())))
        return _DEFAULT_BAR_SECONDS

    def _configured_bar_seconds(self) -> int:
        """Return the configured trading-timeframe duration in seconds."""
        try:
            tf = Timeframe.from_string(self.trading_timeframe)
            return TIMEFRAME_SECONDS.get(tf, _DEFAULT_BAR_SECONDS)
        except ValueError:
            return _DEFAULT_BAR_SECONDS

    @staticmethod
    def _four_tick_offsets_ms(bar_seconds: int) -> npt.NDArray[np.int64]:
        """Return 4 within-bar millisecond offsets."""
        bar_ms = max(1, bar_seconds * 1000)
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
        """Return per-tick spread points for the configured model."""
        if self.spread_model == SPREAD_NATIVE:
            return np.asarray(np.maximum(native_per_tick, 0.0), dtype=np.float64)
        if self.spread_model == SPREAD_FIXED:
            fixed = max(0.0, float(self.fixed_spread_points or 0.0))
            return np.full(total, fixed, dtype=np.float64)
        low = float(self.min_spread_points or 0.0)
        high = float(self.max_spread_points or 0.0)
        rng = RandomGenerator(seed=self._random_seed)
        draws = np.array(
            [rng.next_double(low, high) for _ in range(total)], dtype=np.float64
        )
        return np.asarray(np.maximum(0.0, draws), dtype=np.float64)

    def _four_tick_frame(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Build a 4-tick-per-bar frame from OHLC bars."""
        if bars is None or bars.empty:
            return self._empty_frame()

        bars_indexed = _ensure_datetime_index(bars)
        if not bars_indexed.index.is_monotonic_increasing:
            bars_indexed = bars_indexed.sort_index()

        open_col = self._require_col(bars_indexed, ["Open"], "four-tick generation")
        high_col = self._require_col(bars_indexed, ["High"], "four-tick generation")
        low_col = self._require_col(bars_indexed, ["Low"], "four-tick generation")
        close_col = self._require_col(bars_indexed, ["Close"], "four-tick generation")
        spread_col = self.find_col(bars_indexed, ["Spread"])

        n_bars = len(bars_indexed.index)

        def col_or_zeros(name: str | None) -> npt.NDArray[np.float64]:
            if name is None:
                return np.zeros(n_bars, dtype=np.float64)
            values = pd.to_numeric(bars_indexed[name], errors="coerce").to_numpy(
                dtype=np.float64,
                copy=False,
            )
            return np.asarray(np.nan_to_num(values, nan=0.0), dtype=np.float64)

        open_arr = col_or_zeros(open_col)
        high_arr = col_or_zeros(high_col)
        low_arr = col_or_zeros(low_col)
        close_arr = col_or_zeros(close_col)
        native_spread_arr = col_or_zeros(spread_col)

        bar_seconds = (
            self._infer_bar_seconds(bars_indexed.index)
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
        phases[0::4] = PHASE_OPEN_CODE
        phases[1::4] = np.where(bullish, PHASE_LOW_CODE, PHASE_HIGH_CODE)
        phases[2::4] = np.where(bullish, PHASE_HIGH_CODE, PHASE_LOW_CODE)
        phases[3::4] = PHASE_CLOSE_CODE

        spread_points = self._spread_points(np.repeat(native_spread_arr, 4), total)
        frame: dict[str, Any] = {
            "bid": bid,
            "ask": bid + (spread_points * self.point_value),
            "last": bid,
            "spread": np.rint(np.maximum(spread_points, 0.0)).astype(np.int64),
        }

        repeated_index = bars_indexed.index.repeat(4)
        tick_offsets = pd.to_timedelta(
            np.tile(offsets_ms.astype(np.int64), n_bars),
            unit="ms",
        )
        index = pd.DatetimeIndex(repeated_index + tick_offsets, name="Datetime")
        frame["tick_index_in_bar"] = np.tile(np.array([0, 1, 2, 3]), n_bars)
        frame["is_bar_close"] = phases

        result = pd.DataFrame(frame, index=index, copy=False)
        result["source_bar_time"] = repeated_index
        if not result.index.is_monotonic_increasing:
            return result.sort_index()
        return result

    def _ohlc_m1_frame(
        self,
        _trading_bars: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Build a four-tick frame from M1 bars."""
        if self.m1_bars is None or self.m1_bars.empty:
            raise ValueError("TICK_MODEL_OHLC_M1 requires non-empty m1_bars.")
        return self._four_tick_frame(self.m1_bars)

    def _generated_frame(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Interpolate each trading-timeframe bar into tick-volume ticks."""
        if bars is None or bars.empty:
            return self._empty_frame()

        frame = _ensure_datetime_index(bars)
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
        spread_col = self.find_col(frame, ["Spread"])

        def bar_floats(name: str) -> npt.NDArray[np.float64]:
            values = pd.to_numeric(frame[name], errors="coerce").to_numpy(
                dtype=np.float64,
                copy=False,
            )
            return np.asarray(np.nan_to_num(values, nan=0.0), dtype=np.float64)

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
            return self._empty_frame()

        price, local_i, vol_rep = self._interpolate_generated(
            open_b,
            high_b,
            low_b,
            close_b,
            vol_b=vol_b,
            total=total,
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
            "tick_index_in_bar": local_i,
            "is_bar_close": phases,
        }

        result = pd.DataFrame(data, index=index, copy=False)
        result["source_bar_time"] = repeated_index
        if not result.index.is_monotonic_increasing:
            return result.sort_index()
        return result

    @staticmethod
    def _interpolate_generated(
        open_b: npt.NDArray[np.float64],
        high_b: npt.NDArray[np.float64],
        low_b: npt.NDArray[np.float64],
        close_b: npt.NDArray[np.float64],
        *,
        vol_b: npt.NDArray[np.int64],
        total: int,
    ) -> tuple[
        npt.NDArray[np.float64],
        npt.NDArray[np.int64],
        npt.NDArray[np.int64],
    ]:
        """Vectorize piecewise-linear OHLC interpolation across bars."""
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
        """Return generated tick phase bitmasks."""
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
        bitmask[local_i == 0] |= PHASE_OPEN_CODE
        bitmask[local_i == high_i] |= PHASE_HIGH_CODE
        bitmask[local_i == low_i] |= PHASE_LOW_CODE
        bitmask[local_i == (vol_rep - 1)] |= PHASE_CLOSE_CODE
        return bitmask

    def _real_frame(
        self,
        _trading_bars: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Standardize real ticks."""
        if self.real_ticks is None or self.real_ticks.empty:
            raise ValueError("TICK_MODEL_REAL requires non-empty real_ticks.")

        ticks = _ensure_datetime_index(self.real_ticks.copy())
        bid_col = self._require_col(ticks, ["bid", "Bid"], TICK_MODEL_REAL)
        ask_col = self._require_col(ticks, ["ask", "Ask"], TICK_MODEL_REAL)
        last_col = self.find_col(ticks, ["last", "Last"])
        spread_col = self.find_col(ticks, ["spread", "Spread"])

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
        out["source_bar_time"] = ticks.index
        out["tick_index_in_bar"] = np.arange(len(ticks))
        out["is_bar_close"] = np.full(len(ticks), PHASE_OPEN_CODE, dtype=np.uint8)
        out.index = pd.DatetimeIndex(out.index, name="Datetime")
        return out.sort_index()

    @staticmethod
    def _empty_frame() -> pd.DataFrame:
        """Return an empty tick frame with the standard column layout."""
        columns = [
            "bid",
            "ask",
            "last",
            "spread",
            "source_bar_time",
            "tick_index_in_bar",
            "is_bar_close",
        ]
        return pd.DataFrame(columns=columns)


def _to_dataframe(
    data: pd.DataFrame | list[dict[str, Any]] | None,
) -> pd.DataFrame | None:
    """Coerce list-of-records input into a DataFrame."""
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
) -> pd.DataFrame:
    """Generate standardized ticks as a columnar DataFrame with RangeIndex."""
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


def _output_aware_chunk_bounds(
    counts: npt.NDArray[np.int64],
    max_output_rows: int,
) -> list[tuple[int, int]]:
    """Return input row ranges targeting a maximum generated output size."""
    if len(counts) == 0:
        return []

    target = max(1, max_output_rows)
    bounds: list[tuple[int, int]] = []
    start = 0
    running = 0
    for idx, count in enumerate(counts):
        estimated = max(1, count)
        if idx > start and running + estimated > target:
            bounds.append((start, idx))
            start = idx
            running = 0
        running += estimated
    bounds.append((start, len(counts)))
    return bounds


def _chunk_bounds(n_rows: int, size: int) -> list[tuple[int, int]]:
    """Return row ranges covering n_rows in size chunks."""
    step = max(1, size)
    return [(idx, min(idx + step, n_rows)) for idx in range(0, n_rows, step)]


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
) -> dict[str, Any]:
    """Stream generated ticks to a Parquet file with bounded memory."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        "FR-DATA-BATCH-TICK-GENERATOR: writing ticks to parquet model=%s path=%s",
        model,
        out_path,
    )

    bars_df = _to_dataframe(bars)
    m1_df = _to_dataframe(m1_bars)
    real_df = _to_dataframe(real_ticks)

    source = m1_df if model == TICK_MODEL_OHLC_M1 else bars_df
    if source is None or source.empty:
        empty_frame = generate_ticks(
            model=model,
            trading_timeframe=trading_timeframe,
            bars=bars_df,
            m1_bars=m1_df,
            real_ticks=real_df,
            point_value=point_value,
            spread_model=spread_model,
        )
        empty_frame.to_parquet(out_path, index=False)
        return {
            "path": str(out_path),
            "rows": 0,
            "columns": [str(c) for c in empty_frame.columns],
        }

    writer: pq.ParquetWriter | None = None
    rows = 0
    columns: list[str] = []

    # Calculate chunk boundaries
    if model == TICK_MODEL_GENERATED:
        vol_col = TicksGenerator.find_col(source, ["tick_volume", "Volume", "volume"])
        if vol_col is not None:
            counts = np.maximum(
                4,
                pd.to_numeric(source[vol_col], errors="coerce")
                .fillna(0)
                .to_numpy(dtype=np.int64),
            )
        else:
            counts = np.full(len(source), 4, dtype=np.int64)
        bounds = _output_aware_chunk_bounds(counts, max_output_rows_per_chunk)
    else:
        rows_per_chunk = max(1, max_output_rows_per_chunk // 4)
        bounds = _chunk_bounds(len(source), min(chunk_size, rows_per_chunk))

    try:
        for start, stop in bounds:
            piece = source.iloc[start:stop]
            piece_bars = bars_df if model == TICK_MODEL_OHLC_M1 else piece
            piece_m1 = piece if model == TICK_MODEL_OHLC_M1 else m1_df

            chunk_frame = generate_ticks(
                model=model,
                trading_timeframe=trading_timeframe,
                bars=piece_bars,
                m1_bars=piece_m1,
                real_ticks=real_df,
                point_value=point_value,
                spread_model=spread_model,
                fixed_spread_points=fixed_spread_points,
                min_spread_points=min_spread_points,
                max_spread_points=max_spread_points,
                random_seed=random_seed,
            )
            if chunk_frame.empty:
                continue

            table = pa.Table.from_pandas(chunk_frame, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(out_path, table.schema)
                columns = [str(c) for c in chunk_frame.columns]
            writer.write_table(table)
            rows += len(chunk_frame)
    finally:
        if writer is not None:
            writer.close()

    return {"path": str(out_path), "rows": rows, "columns": columns}


def main() -> None:
    """Demonstrate vectorized tick generation from synthetic OHLC DataFrame."""
    idx = pd.date_range("2024-01-01", periods=3, freq="1min", tz="UTC")
    df = pd.DataFrame(
        {
            "Open": [1.1000, 1.1020, 1.1010],
            "High": [1.1050, 1.1060, 1.1030],
            "Low": [1.0990, 1.1000, 1.0980],
            "Close": [1.1020, 1.1010, 1.1025],
            "Volume": [100, 150, 120],
        },
        index=idx,
    )
    df.index.name = "Datetime"
    ticks_df = generate_ticks(
        bars=df,
        m1_bars=df,
        model=TICK_MODEL_OHLC_M1,
        trading_timeframe="M1",
    )
    print(f"Generated {len(ticks_df)} ticks using OHLC M1 model.")


if __name__ == "__main__":
    main()
