"""Smart Money Concepts indicator implementations and official AI Tools.

SMC calculations can be sensitive to lookahead. This production rewrite uses
explicit parameters to separate confirmed backtest-safe signals from historical
annotation-style outputs:

- ``confirmed_only=True`` shifts/derives SMC outputs so the current bar does not
  depend on future bars.
- ``confirmed_only=False`` may produce historical labels useful for chart review,
  but should not be consumed as same-bar trading signals.

Classes:
    None.

Functions:
    calculate_fvg_frame: Internal Fair Value Gap implementation.
    calculate_swing_highs_lows_frame: Internal swing high/low implementation.
    calculate_bos_choch_frame: Internal BOS/CHOCH implementation.
    calculate_ob_frame: Internal order block implementation.
    calculate_previous_high_low_frame: Internal previous high/low implementation.
    fvg: Official AI Tool for Fair Value Gaps.
    swing_highs_lows: Official AI Tool for swing highs/lows.
    bos_choch: Official AI Tool for BOS/CHOCH.
    ob: Official AI Tool for order blocks.
    previous_high_low: Official AI Tool for prior high/low context.

Exported AI Tools:
    fvg, swing_highs_lows, bos_choch, ob, previous_high_low.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from tools.utils.standard import ToolSpec, run_indicator_tool
from tools.utils.validators import (
    ensure_dataframe,
    require_columns,
    require_positive_int,
)

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "indicators"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


def _normalized_ohlcv(data: Any, *, require_volume: bool = False) -> pd.DataFrame:
    frame = ensure_dataframe(data)
    frame = frame.rename(
        columns={column: str(column).lower() for column in frame.columns}
    )
    required = ["open", "high", "low", "close"]
    if require_volume:
        required.append("volume")
    require_columns(frame, required)
    return frame


def calculate_fvg_frame(
    data: Any,
    *,
    join_consecutive: bool = False,
    confirmed_only: bool = True,
) -> pd.DataFrame:
    """Calculate Fair Value Gap columns.

    When ``confirmed_only=True``, the FVG is assigned to the confirmation bar
    instead of the middle candle, avoiding same-bar future leakage.
    """
    frame = _normalized_ohlcv(data)
    result = frame.copy()

    bullish = (frame["high"].shift(2) < frame["low"]) & (
        frame["close"].shift(1) > frame["open"].shift(1)
    )
    bearish = (frame["low"].shift(2) > frame["high"]) & (
        frame["close"].shift(1) < frame["open"].shift(1)
    )

    direction = pd.Series(np.nan, index=frame.index, dtype="float64")
    direction.loc[bullish] = 1.0
    direction.loc[bearish] = -1.0
    top = pd.Series(np.nan, index=frame.index, dtype="float64")
    bottom = pd.Series(np.nan, index=frame.index, dtype="float64")
    top.loc[bullish] = frame.loc[bullish, "low"]
    bottom.loc[bullish] = frame["high"].shift(2).loc[bullish]
    top.loc[bearish] = frame["low"].shift(2).loc[bearish]
    bottom.loc[bearish] = frame.loc[bearish, "high"]

    if join_consecutive:
        for idx in range(1, len(direction)):
            if direction.iloc[idx] == direction.iloc[idx - 1] and pd.notna(
                direction.iloc[idx]
            ):
                top.iloc[idx] = max(top.iloc[idx - 1], top.iloc[idx])
                bottom.iloc[idx] = min(bottom.iloc[idx - 1], bottom.iloc[idx])
                direction.iloc[idx - 1] = np.nan
                top.iloc[idx - 1] = np.nan
                bottom.iloc[idx - 1] = np.nan

    mitigated_index = pd.Series(pd.NA, index=frame.index, dtype="object")
    for position in np.where(direction.notna())[0]:
        future = frame.iloc[position + 1 :]
        if future.empty:
            continue
        if direction.iloc[position] == 1.0:
            hits = future[future["low"] <= top.iloc[position]]
        else:
            hits = future[future["high"] >= bottom.iloc[position]]
        if not hits.empty:
            mitigated_index.iloc[position] = hits.index[0]

    if not confirmed_only:
        direction = direction.shift(-1)
        top = top.shift(-1)
        bottom = bottom.shift(-1)
        mitigated_index = mitigated_index.shift(-1)

    result["fvg"] = direction
    result["fvg_top"] = top
    result["fvg_bottom"] = bottom
    result["fvg_mitigated_index"] = mitigated_index
    result["fvg_lookahead_safe"] = confirmed_only
    return result


def calculate_swing_highs_lows_frame(
    data: Any,
    *,
    swing_length: int = 5,
    confirmed_only: bool = True,
) -> pd.DataFrame:
    """Calculate swing high and swing low columns.

    Confirmed mode shifts detected pivots by ``swing_length`` bars so the signal
    is only visible after the right-side confirmation window has closed.
    """
    require_positive_int(swing_length, name="swing_length")
    frame = _normalized_ohlcv(data)
    result = frame.copy()
    window = (2 * swing_length) + 1
    rolling_high = frame["high"].rolling(window=window, center=True).max()
    rolling_low = frame["low"].rolling(window=window, center=True).min()

    swing_high = (
        (frame["high"] == rolling_high)
        .astype(float)
        .where(frame["high"] == rolling_high)
    )
    swing_low = (
        (frame["low"] == rolling_low).astype(float).where(frame["low"] == rolling_low)
    )
    level = pd.Series(np.nan, index=frame.index, dtype="float64")
    level.loc[swing_high.notna()] = frame.loc[swing_high.notna(), "high"]
    level.loc[swing_low.notna()] = frame.loc[swing_low.notna(), "low"]

    if confirmed_only:
        swing_high = swing_high.shift(swing_length)
        swing_low = swing_low.shift(swing_length)
        level = level.shift(swing_length)

    result["swing_high"] = swing_high
    result["swing_low"] = swing_low
    result["swing_level"] = level
    result["swing_lookahead_safe"] = confirmed_only
    return result


def calculate_bos_choch_frame(
    data: Any,
    *,
    swing_length: int = 5,
    close_break: bool = True,
    confirmed_only: bool = True,
) -> pd.DataFrame:
    """Calculate simplified BOS/CHOCH columns from confirmed swings."""
    frame = calculate_swing_highs_lows_frame(
        data, swing_length=swing_length, confirmed_only=confirmed_only
    )
    result = frame.copy()
    break_source_high = result["close"] if close_break else result["high"]
    break_source_low = result["close"] if close_break else result["low"]
    last_swing_high = result["swing_level"].where(result["swing_high"].notna()).ffill()
    last_swing_low = result["swing_level"].where(result["swing_low"].notna()).ffill()

    bullish_bos = break_source_high > last_swing_high.shift(1)
    bearish_bos = break_source_low < last_swing_low.shift(1)
    trend = pd.Series(0, index=result.index, dtype="int64")
    trend.loc[bullish_bos] = 1
    trend.loc[bearish_bos] = -1
    previous_trend = trend.replace(0, pd.NA).ffill().shift(1)

    result["bos"] = pd.Series(np.nan, index=result.index, dtype="float64")
    result.loc[bullish_bos, "bos"] = 1.0
    result.loc[bearish_bos, "bos"] = -1.0
    result["choch"] = pd.Series(np.nan, index=result.index, dtype="float64")
    result.loc[bullish_bos & (previous_trend == -1), "choch"] = 1.0
    result.loc[bearish_bos & (previous_trend == 1), "choch"] = -1.0
    result["bos_choch_level"] = pd.NA
    result.loc[bullish_bos, "bos_choch_level"] = last_swing_high.shift(1).loc[
        bullish_bos
    ]
    result.loc[bearish_bos, "bos_choch_level"] = last_swing_low.shift(1).loc[
        bearish_bos
    ]
    result["bos_choch_lookahead_safe"] = confirmed_only
    return result


def calculate_ob_frame(
    data: Any,
    *,
    swing_length: int = 5,
    confirmed_only: bool = True,
) -> pd.DataFrame:
    """Calculate simplified order block columns from BOS events."""
    frame = calculate_bos_choch_frame(
        data, swing_length=swing_length, close_break=True, confirmed_only=confirmed_only
    )
    result = frame.copy()
    bullish = result["bos"] == 1.0
    bearish = result["bos"] == -1.0
    result["ob"] = pd.Series(np.nan, index=result.index, dtype="float64")
    result.loc[bullish, "ob"] = 1.0
    result.loc[bearish, "ob"] = -1.0
    result["ob_top"] = pd.NA
    result["ob_bottom"] = pd.NA
    result.loc[bullish, "ob_top"] = result["high"].shift(1).loc[bullish]
    result.loc[bullish, "ob_bottom"] = result["low"].shift(1).loc[bullish]
    result.loc[bearish, "ob_top"] = result["high"].shift(1).loc[bearish]
    result.loc[bearish, "ob_bottom"] = result["low"].shift(1).loc[bearish]
    result["ob_lookahead_safe"] = confirmed_only
    return result


def calculate_previous_high_low_frame(data: Any, *, period: int = 1) -> pd.DataFrame:
    """Calculate previous rolling high and low context without lookahead."""
    require_positive_int(period, name="period")
    frame = _normalized_ohlcv(data)
    result = frame.copy()
    result[f"previous_high_{period}"] = frame["high"].rolling(period).max().shift(1)
    result[f"previous_low_{period}"] = frame["low"].rolling(period).min().shift(1)
    return result


def fvg(
    data: Any,
    join_consecutive: bool = False,
    confirmed_only: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate Fair Value Gaps as an official agent-callable tool."""
    return run_indicator_tool(
        ToolSpec(tool_name="fvg"),
        lambda: calculate_fvg_frame(
            data, join_consecutive=join_consecutive, confirmed_only=confirmed_only
        ),
        request_id=request_id,
    )


def swing_highs_lows(
    data: Any,
    swing_length: int = 5,
    confirmed_only: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate confirmed swing highs and lows as an AI Tool."""
    return run_indicator_tool(
        ToolSpec(tool_name="swing_highs_lows"),
        lambda: calculate_swing_highs_lows_frame(
            data, swing_length=swing_length, confirmed_only=confirmed_only
        ),
        request_id=request_id,
    )


def bos_choch(
    data: Any,
    swing_length: int = 5,
    close_break: bool = True,
    confirmed_only: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate BOS/CHOCH as an official agent-callable SMC tool."""
    return run_indicator_tool(
        ToolSpec(tool_name="bos_choch"),
        lambda: calculate_bos_choch_frame(
            data,
            swing_length=swing_length,
            close_break=close_break,
            confirmed_only=confirmed_only,
        ),
        request_id=request_id,
    )


def ob(
    data: Any,
    swing_length: int = 5,
    confirmed_only: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate simplified order blocks as an official AI Tool."""
    return run_indicator_tool(
        ToolSpec(tool_name="ob"),
        lambda: calculate_ob_frame(
            data, swing_length=swing_length, confirmed_only=confirmed_only
        ),
        request_id=request_id,
    )


def previous_high_low(
    data: Any,
    period: int = 1,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate previous high/low context as a lookahead-safe AI Tool."""
    return run_indicator_tool(
        ToolSpec(tool_name="previous_high_low"),
        lambda: calculate_previous_high_low_frame(data, period=period),
        request_id=request_id,
    )
