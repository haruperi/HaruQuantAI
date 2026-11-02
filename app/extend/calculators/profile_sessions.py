"""Causal session scheduling for the donor's volume and TPO calculations.

Description:
    Computes session windows, intraday boundary timestamps, custom hours
    segmentation, and rolling daily/weekly/monthly slices for market profile
    indicators.
Purpose:
    FEAT-CALCULATORS: Session profile calculation kernels.
Key Capabilities:
    - FR-CALC-PROFILE-SESSIONS: Session boundary partitioning and calendar scheduling.
Python API Usage:
    from app.extend.calculators.profile_sessions import calculate_sessions
CLI Usage:
    uv run pytest tests/extend/blocks/test_profile_sessions.py --no-cov
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np

from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.calculators.profile import (
    TPO_OUTPUTS,
    VOLUME_OUTPUTS,
    tpo_profile,
    volume_profile,
)

SUNDAY = 6
WEEKLY = 2
MONTHLY = 3
DECEMBER = 12
ACTUAL_DAY = 5
PREVIOUS_SWING = 9
ACTUAL_SWING = 10
FIXED_TICKS = 2
ATR_MULTIPLE = 3


def session_bounds(
    now: int,
    kind: int,
    zone: ZoneInfo,
    custom: tuple[int, int] | None = None,
    *,
    advance_gap: bool = True,
) -> tuple[int, int]:
    """Calendar bounds in chart timezone; custom windows can cross midnight."""
    dt = datetime.fromtimestamp(now / 1000, UTC).astimezone(zone)
    day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if kind == 1:
        if custom is not None:
            start = day + timedelta(minutes=custom[0])
            end = day + timedelta(minutes=custom[1])
            if end <= start:
                end += timedelta(days=1)
            if dt < start:
                start -= timedelta(days=1)
                end -= timedelta(days=1)
            if advance_gap and dt >= end:
                start += timedelta(days=1)
                end += timedelta(days=1)
        else:
            start = day - timedelta(days=2) if day.weekday() == SUNDAY else day
            end = start + timedelta(days=1)
    elif kind == WEEKLY:
        start = day - timedelta(days=day.weekday())
        end = start + timedelta(days=7)
    elif kind == MONTHLY:
        start = day.replace(day=1)
        end = (
            start.replace(year=start.year + 1, month=1)
            if start.month == DECEMBER
            else start.replace(month=start.month + 1)
        )
    else:
        start = day.replace(month=1, day=1)
        end = start.replace(year=start.year + 1)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def _calendar_events(
    times: np.ndarray[Any, Any],
    config: Mapping[str, Any],
    zone: ZoneInfo,
    custom: tuple[int, int] | None,
    *,
    multi: bool,
) -> Iterator[tuple[int, int, int]]:
    selection = config["session_type"]
    kind = (selection - 1) % 4 + 1
    actual = selection >= ACTUAL_DAY
    current_start = current_end = 0
    for i, timestamp in enumerate(times):
        now = int(timestamp)
        if current_end == 0 or now >= current_end:
            previous_start, previous_end = current_start, current_end
            current_start, current_end = session_bounds(
                now,
                kind,
                zone,
                custom,
                advance_gap=not config.get("tpo", False) or multi,
            )
            if custom is not None and not config.get("tpo", False):
                dt = datetime.fromtimestamp(current_start / 1000, UTC).astimezone(zone)
                if dt.weekday() == SUNDAY:
                    current_start = int((dt - timedelta(days=2)).timestamp() * 1000)
                    end_dt = datetime.fromtimestamp(current_end / 1000, UTC).astimezone(
                        zone
                    )
                    current_end = int((end_dt - timedelta(days=2)).timestamp() * 1000)
            if not actual and previous_start > 0:
                if (
                    datetime.fromtimestamp(previous_start / 1000, UTC)
                    .astimezone(zone)
                    .weekday()
                    == SUNDAY
                ):
                    dt = datetime.fromtimestamp(previous_start / 1000, UTC).astimezone(
                        zone
                    ).replace(hour=0, minute=0) - timedelta(days=2)
                    previous_start = int(dt.timestamp() * 1000)
                    previous_end = int((dt + timedelta(days=1)).timestamp() * 1000)
                yield i, previous_start, previous_end
        if (
            actual
            and current_start > 0
            and now > current_start
            and (not multi or now < current_end)
        ):
            yield i, current_start, min(current_end, now)


# Keep confirmation and state mutation in donor order; never backfill pivots.
def _swing_events(  # noqa: C901, PLR0912
    bars: BarData, times: np.ndarray[Any, Any], config: Mapping[str, Any]
) -> Iterator[tuple[int, int, int]]:
    direction = 0
    pivot_high = pivot_low = 0.0
    high_time = low_time = session_start = 0
    for i, timestamp in enumerate(times):
        now = int(timestamp)
        high, low = float(bars.high[i]), float(bars.low[i])
        if direction == 0:
            pivot_high, pivot_low, high_time, low_time, session_start, direction = (
                high,
                low,
                now,
                now,
                now,
                1,
            )
            continue
        method = config["pivot_method"]
        if method == FIXED_TICKS:
            threshold = config["pivot_ticks"] * config["tick_size"]
        elif method == ATR_MULTIPLE:
            available = min(config["pivot_atr_period"], i)
            total = 0.0
            for j in range(i, i - available, -1):
                total += max(
                    bars.high[j] - bars.low[j],
                    abs(bars.high[j] - bars.close[j - 1]),
                    abs(bars.low[j] - bars.close[j - 1]),
                )
            threshold = total / available * config["pivot_atr_multiple"]
        else:
            reference = pivot_high if direction == 1 else pivot_low
            threshold = (
                (reference if reference > 0 else bars.close[i])
                * config["pivot_pct"]
                / 100
            )
        confirmed = False
        pivot_time = 0
        if direction == 1:
            if high > pivot_high:
                pivot_high, high_time = high, now
            if pivot_high - low >= threshold:
                pivot_time, direction, pivot_low, low_time, confirmed = (
                    high_time,
                    -1,
                    low,
                    now,
                    True,
                )
        else:
            if low < pivot_low:
                pivot_low, low_time = low, now
            if high - pivot_low >= threshold:
                pivot_time, direction, pivot_high, high_time, confirmed = (
                    low_time,
                    1,
                    high,
                    now,
                    True,
                )
        actual = config["session_type"] == ACTUAL_SWING
        if confirmed and session_start > 0 and (actual or pivot_time > session_start):
            yield i, session_start, pivot_time
            session_start = pivot_time
        if actual and session_start > 0 and now > session_start:
            yield i, session_start, now


# One ordered replay owns output carry-forward and per-session state.
def calculate_sessions(  # noqa: C901, PLR0912, PLR0915
    bars: BarData,
    config: Mapping[str, Any],
    *,
    tpo: bool = False,
    custom: tuple[int, int] | None = None,
    multi: bool = False,
) -> dict[str, IndicatorSeries]:
    """Batch replay of the donor state machine; completed sessions calculate once."""
    bars.require_inputs(("open", "high", "low", "close", "volume"))
    count = len(bars.close)
    times = bars.timestamps
    if len(times) != count:
        raise ValueError("Profile calculations require aligned timestamps")
    if len(times) and (np.any(times <= 0) or np.any(np.diff(times) <= 0)):
        raise ValueError("Profile timestamps must be positive and strictly increasing")
    if config["timestamp_unit"] == "seconds":
        times = times * 1000
    zone = ZoneInfo(config["timezone"])
    tick_size = config["tick_size"]
    if (
        config["bin_size_mode"] == FIXED_TICKS
        or (
            config["session_type"] >= PREVIOUS_SWING
            and config.get("pivot_method") == FIXED_TICKS
        )
    ) and tick_size is None:
        raise ValueError("tick_size is required for fixed-tick bins or pivots")
    for name in ("open", "high", "low", "close", "volume"):
        if not np.isfinite(getattr(bars, name)).all():
            raise ValueError(f"Profile {name} must contain only finite values")
    if np.any(bars.high < bars.low) or np.any(bars.volume < 0):
        raise ValueError("Profile bars require high >= low and nonnegative volume")
    keys = TPO_OUTPUTS if tpo else VOLUME_OUTPUTS
    arrays = {key: np.zeros(count) for key in keys}
    state = dict.fromkeys(keys, 0.0)
    if tpo:
        state["profile_shape"] = 5.0
    weekdays = np.array(
        [
            datetime.fromtimestamp(int(t) / 1000, UTC).astimezone(zone).weekday()
            for t in times
        ]
    )
    options = dict(config, tpo=tpo)
    events = (
        _swing_events(bars, times, config)
        if config["session_type"] >= PREVIOUS_SWING
        else _calendar_events(times, options, zone, custom, multi=multi)
    )
    previous_poc_index = -1
    written = 0
    for i, start, end in events:
        for key in keys:
            arrays[key][written:i] = state[key]
        written = i
        left = int(np.searchsorted(times, start))
        right = min(i + 1, int(np.searchsorted(times, end)))
        indices = np.arange(left, right)
        indices = indices[weekdays[left:right] != SUNDAY]
        if not len(indices) or np.max(bars.high[indices]) <= np.min(bars.low[indices]):
            continue
        high, low, open_, close, volume = (
            getattr(bars, name)[indices]
            for name in ("high", "low", "open", "close", "volume")
        )
        kwargs = {
            "rows": config["profile_rows"],
            "fraction": config["value_area_pct"] / 100.0,
            "tick_width": tick_size * config["ticks_per_bin"]
            if config["bin_size_mode"] == FIXED_TICKS
            else 0.0,
        }
        kind = (
            (config["session_type"] - 1) % 4 + 1
            if config["session_type"] < PREVIOUS_SWING
            else 1
        )
        if tpo:
            # Donor skips Sunday bars before updating nextBarTime.
            ends = np.full(len(indices), end, dtype=np.int64)
            ends[:-1] = times[indices[1:]]
            result, previous_poc_index = tpo_profile(
                high,
                low,
                open_,
                close,
                volume,
                times[indices],
                start=start,
                end=end,
                bracket_minutes=config[
                    (
                        "bracket_min_daily",
                        "bracket_min_weekly",
                        "bracket_min_monthly",
                        "bracket_min_yearly",
                    )[kind - 1]
                ],
                previous_poc_index=previous_poc_index,
                bar_ends=ends,
                **kwargs,
            )
        else:
            result = volume_profile(
                high,
                low,
                open_,
                close,
                volume,
                hvn_count=config["hvn_count"],
                hvn_threshold=config["hvn_threshold_pct"] / 100.0,
                lvn_threshold=config["lvn_threshold_pct"] / 100.0,
                enable_lvn=config["enable_lvn"],
                enable_vcp=config["enable_vcp"],
                cluster_spread=config["cluster_spread"],
                max_cluster_centers=config["max_cluster_centers"],
                **kwargs,
            )
            result["delta_poc"] = (
                result["poc"] - state["poc"] if state["poc"] != 0 else 0.0
            )
            previous_mid = (state["vah"] + state["val"]) / 2
            result["delta_va"] = (
                (result["vah"] + result["val"]) / 2 - previous_mid
                if previous_mid != 0
                else 0.0
            )
        minutes = (
            (60, 720, 1440, 8640)[kind - 1]
            if tpo or config["ib_minutes"] == 0
            else config["ib_minutes"]
        )
        initial = times[indices] < start + minutes * 60_000
        if initial.any() and np.max(high[initial]) > np.min(low[initial]):
            result["ib_high" if tpo else "ibh"] = float(np.max(high[initial]))
            result["ib_low" if tpo else "ibl"] = float(np.min(low[initial]))
        state.update(result)
    for key in keys:
        arrays[key][written:] = state[key]
    return {
        key: IndicatorSeries(values, name=key.upper()) for key, values in arrays.items()
    }
