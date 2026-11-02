"""Session histogram calculations shared by volume and time-price profiles.

Description:
    Computes volume and Time-Price-Opportunity (TPO) session profiles, value
    area thresholds (VAH, VAL, POC), volume-weighted node distributions, and
    shape classifications with newest-first accumulation.
Purpose:
    FEAT-CALCULATORS: Session profile calculation kernels.
Key Capabilities:
    - FR-CALC-PROFILE: Volume and TPO profile binning, value areas, and node statistics.
Python API Usage:
    from app.extend.calculators.profile import calculate_profile
CLI Usage:
    uv run pytest tests/extend/blocks/test_profile_sessions.py --no-cov
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

Array = np.ndarray[Any, Any]
MIN_SHAPE_BINS = 3
MIN_VALLEY_BINS = 2
MIN_CLUSTER_TPOS = 3
TOP_THIRD = 0.66
BOTTOM_THIRD = 0.33
BALANCED_RATIO = 0.6
MIN_LEDGE_BINS = 3
POOR_EXTREME_TPOS = 2
VOLUME_OUTPUTS = (
    "poc",
    "vah",
    "val",
    "ibh",
    "ibl",
    *(f"hvn{i}" for i in range(1, 6)),
    *(f"lvn{i}" for i in range(1, 6)),
    "vpoc",
    "vvah",
    "vval",
    "bull_poc",
    "bear_poc",
    "total_volume",
    "total_bull_volume",
    "total_bear_volume",
    "delta",
    "delta_poc",
    "delta_va",
    "profile_range",
    "poc_pct_up",
    "poc_pct_down",
)
TPO_OUTPUTS = (
    "poc",
    "vah",
    "val",
    "poor_high",
    "poor_low",
    "excess_high",
    "excess_low",
    "single_prints",
    "buying_tail_len",
    "selling_tail_len",
    "profile_shape",
    "ledge_up",
    "ledge_down",
    "ib_high",
    "ib_low",
    "vpoc",
    "vvah",
    "vval",
    "bull_poc",
    "bear_poc",
    "total_volume",
    "total_bull_volume",
    "total_bear_volume",
)


def value_area(
    bins: Array,
    fraction: float,
    *,
    lower_ties: bool = False,
    total: float | None = None,
) -> tuple[int, int]:
    """Expand from the first maximum; raw profiles prefer up on ties, VCP down."""
    lower = upper = int(np.argmax(bins))
    accumulated = float(bins[lower])
    target = (sum(float(x) for x in bins) if total is None else total) * fraction
    while accumulated < target and (lower > 0 or upper < len(bins) - 1):
        below = float(bins[lower - 1]) if lower > 0 else -1.0
        above = float(bins[upper + 1]) if upper + 1 < len(bins) else -1.0
        if below > above or (lower_ties and below == above):
            lower -= 1
            accumulated += float(bins[lower])
        else:
            upper += 1
            accumulated += float(bins[upper])
    return lower, upper


def profile_grid(
    high: Array, low: Array, rows: int, tick_width: float
) -> tuple[float, float, int]:
    """Donor fixed bins cap at 2000 without changing the configured tick width."""
    bottom = float(np.min(low))
    extent = float(np.max(high)) - bottom
    width = tick_width if tick_width > 0 else extent / rows
    count = max(1, min(2000, math.ceil(extent / width))) if tick_width > 0 else rows
    return bottom, width, count


def histogram_levels(
    bins: Array,
    bottom: float,
    width: float,
    fraction: float,
    *,
    lower_ties: bool = False,
    total: float | None = None,
) -> tuple[float, float, float]:
    """Return POC, VAH, VAL for a nonempty histogram."""
    lo, hi = value_area(bins, fraction, lower_ties=lower_ties, total=total)
    return (
        bottom + (int(np.argmax(bins)) + 0.5) * width,
        bottom + (hi + 1) * width,
        bottom + lo * width,
    )


# Keep the donor candidate-selection order explicit for numerical qualification.
def _nodes(bins: Array, *, count: int, threshold: float, valleys: bool) -> list[int]:  # noqa: C901
    maximum = float(np.max(bins))
    if maximum <= 0:
        return []
    candidates = []
    for j, value in enumerate(bins):
        if valleys:
            if (
                0 < j < len(bins) - 1
                and value <= maximum * threshold
                and value < bins[j - 1]
                and value < bins[j + 1]
            ):
                candidates.append(j)
        elif j != int(np.argmax(bins)) and value >= maximum * threshold:
            left = bins[j - 1] if j else -1
            right = bins[j + 1] if j + 1 < len(bins) else -1
            if value > left and value > right:
                candidates.append(j)
    # Match the donor's selection sort, including how equal candidates move.
    for a in range(len(candidates) - 1):
        best = a
        for b in range(a + 1, len(candidates)):
            if (
                (bins[candidates[b]] < bins[candidates[best]])
                if valleys
                else (bins[candidates[b]] > bins[candidates[best]])
            ):
                best = b
        candidates[a], candidates[best] = candidates[best], candidates[a]
    accepted: list[int] = []
    for j in candidates:
        if not valleys and any(
            min(bins[min(j, k) + 1 : max(j, k)], default=math.inf)
            >= min(bins[j], bins[k]) * 0.5
            for k in accepted
        ):
            continue
        accepted.append(j)
        if len(accepted) == min(count, 5):
            break
    return accepted


# Ordered histogram, node and cluster passes mirror the donor calculation.
def volume_profile(  # noqa: C901
    high: Array,
    low: Array,
    open_: Array,
    close: Array,
    volume: Array,
    *,
    rows: int,
    fraction: float,
    tick_width: float,
    hvn_count: int,
    hvn_threshold: float,
    lvn_threshold: float,
    enable_lvn: bool,
    enable_vcp: bool,
    cluster_spread: float,
    max_cluster_centers: int,
) -> dict[str, float]:
    """Compute the donor volume histogram, directional totals, nodes and clusters."""
    bottom, width, count = profile_grid(high, low, rows, tick_width)
    bins = np.zeros(count)
    bull = np.zeros(count)
    bear = np.zeros(count)
    total = bull_total = bear_total = 0.0
    for i in range(len(high) - 1, -1, -1):
        lo = max(0, min(count - 1, int(((low[i] - bottom) * 1000) / (width * 1000))))
        hi = max(0, min(count - 1, int(((high[i] - bottom) * 1000) / (width * 1000))))
        amount = float(volume[i])
        part = amount / (hi - lo + 1)
        bins[lo : hi + 1] += part
        total += amount
        if close[i] >= open_[i]:
            bull[lo : hi + 1] += part
            bull_total += amount
        else:
            bear[lo : hi + 1] += part
            bear_total += amount
    poc, vah, val = histogram_levels(bins, bottom, width, fraction, total=total)
    result = {
        "poc": poc,
        "vah": vah,
        "val": val,
        "vpoc": poc,
        "vvah": vah,
        "vval": val,
        "bull_poc": bottom + (int(np.argmax(bull)) + 0.5) * width
        if bull_total > 0
        else 0.0,
        "bear_poc": bottom + (int(np.argmax(bear)) + 0.5) * width
        if bear_total > 0
        else 0.0,
        "total_volume": total,
        "total_bull_volume": bull_total,
        "total_bear_volume": bear_total,
        "delta": bull_total - bear_total,
        "profile_range": float(np.max(high)) - bottom,
    }
    result["poc_pct_up"] = (float(np.max(high)) - poc) / result["profile_range"] * 100
    result["poc_pct_down"] = (poc - bottom) / result["profile_range"] * 100
    for prefix, enabled, threshold in (
        ("hvn", True, hvn_threshold),
        ("lvn", enable_lvn, lvn_threshold),
    ):
        nodes = (
            _nodes(bins, count=hvn_count, threshold=threshold, valleys=prefix == "lvn")
            if enabled
            else []
        )
        for i in range(5):
            result[f"{prefix}{i + 1}"] = (
                bottom + (nodes[i] + 0.5) * width if i < len(nodes) else 0.0
            )
    if enable_vcp:
        peaks = [
            j
            for j in range(count)
            if bins[j] > total / count
            and (j == 0 or bins[j] >= bins[j - 1])
            and (j == count - 1 or bins[j] >= bins[j + 1])
        ]
        for a in range(min(max_cluster_centers, len(peaks))):
            best = a
            for b in range(a + 1, len(peaks)):
                if bins[peaks[b]] > bins[peaks[best]]:
                    best = b
            peaks[a], peaks[best] = peaks[best], peaks[a]
        if peaks:
            clustered = np.zeros(count)
            for center in peaks[:max_cluster_centers]:
                for j in range(count):
                    distance = (j - center) / cluster_spread
                    clustered[j] += bins[center] * math.exp(-0.5 * distance * distance)
            result["vpoc"], result["vvah"], result["vval"] = histogram_levels(
                clustered, bottom, width, fraction, lower_ties=True
            )
    return result


def _shape(bins: Array, low: int, high: int, previous_poc_index: int) -> int:
    """Preserve donor ordering: shape uses the previous calculation's POC index."""
    active = high - low + 1
    if active < MIN_SHAPE_BINS:
        return 5
    valley_start = -1
    for j in range(low + active // 4, high - active // 4 + 2):
        if j <= high - active // 4 and bins[j] <= 1:
            if valley_start < 0:
                valley_start = j
        else:
            if (
                valley_start >= 0
                and j - valley_start >= MIN_VALLEY_BINS
                and sum(bins[low:valley_start]) >= MIN_CLUSTER_TPOS
                and sum(bins[j : high + 1]) >= MIN_CLUSTER_TPOS
            ):
                return 4
            valley_start = -1
    relative = (previous_poc_index - low) / (active - 1)
    third = active // 3
    bottom_avg = float(sum(bins[low : low + third])) / max(1, third)
    top_avg = float(sum(bins[high - third + 1 : high + 1])) / max(1, third)
    if relative > TOP_THIRD and top_avg > bottom_avg * 1.5:
        return 1
    if relative < BOTTOM_THIRD and bottom_avg > top_avg * 1.5:
        return 2
    if BOTTOM_THIRD <= relative <= TOP_THIRD:
        mid = low + active // 2
        below, above = float(sum(bins[low:mid])), float(sum(bins[mid : high + 1]))
        if min(below, above) / max(1.0, below, above) > BALANCED_RATIO:
            return 3
    return 5


# Preserve bracket-mask and structure-analysis pass order from the donor.
def tpo_profile(  # noqa: C901, PLR0912, PLR0917
    high: Array,
    low: Array,
    open_: Array,
    close: Array,
    volume: Array,
    times: Array,
    *,
    start: int,
    end: int,
    rows: int,
    fraction: float,
    tick_width: float,
    bracket_minutes: int,
    previous_poc_index: int,
    bar_ends: Array,
) -> tuple[dict[str, float], int]:
    """One TPO per bracket per price bin; directional counts remain per bar."""
    bottom, width, count = profile_grid(high, low, rows, tick_width)
    masks = [0] * count
    bull, bear = np.zeros(count), np.zeros(count)
    total = bull_total = bear_total = 0.0
    for i in range(len(high) - 1, -1, -1):
        first = max(0, min(61, int((times[i] - start) // (bracket_minutes * 60_000))))
        last = max(
            0,
            min(
                61,
                int(
                    (max(min(int(bar_ends[i]), end) - 1, int(times[i])) - start)
                    // (bracket_minutes * 60_000)
                ),
            ),
        )
        bits = ((1 << (last - first + 1)) - 1) << first
        lo = max(0, min(count - 1, int((low[i] - bottom) / width)))
        hi = max(0, min(count - 1, int((high[i] - bottom) / width)))
        for j in range(lo, hi + 1):
            masks[j] |= bits
        amount = float(volume[i])
        total += amount
        if close[i] >= open_[i]:
            bull[lo : hi + 1] += 1
            bull_total += amount
        else:
            bear[lo : hi + 1] += 1
            bear_total += amount
    bins = np.array([mask.bit_count() for mask in masks])
    occupied = np.flatnonzero(bins)
    lo, hi = int(occupied[0]), int(occupied[-1])
    buy_tail = sell_tail = 0
    for j in range(lo, hi + 1):
        if bins[j] != 1:
            break
        buy_tail += 1
    for j in range(hi, lo - 1, -1):
        if bins[j] != 1:
            break
        sell_tail += 1
    up_len = down_len = 0
    up_price = down_price = 0.0
    run_start = lo
    for j in range(lo + 1, hi + 1):
        if bins[j] == bins[run_start] and bins[j] > 0:
            length = j - run_start + 1
            mid = lo + (hi - lo) // 2
            if j >= mid and length > up_len and length >= MIN_LEDGE_BINS:
                up_len, up_price = length, bottom + (j + 0.5) * width
            if run_start <= mid and length > down_len and length >= MIN_LEDGE_BINS:
                down_len, down_price = length, bottom + (run_start + 0.5) * width
        else:
            run_start = j
    poc, vah, val = histogram_levels(bins, bottom, width, fraction)
    return {
        "poc": poc,
        "vah": vah,
        "val": val,
        "vpoc": poc,
        "vvah": vah,
        "vval": val,
        "poor_high": float(bins[hi] >= POOR_EXTREME_TPOS),
        "poor_low": float(bins[lo] >= POOR_EXTREME_TPOS),
        "excess_high": float(bins[hi] == 1),
        "excess_low": float(bins[lo] == 1),
        "single_prints": float(np.count_nonzero(bins == 1)),
        "buying_tail_len": float(buy_tail),
        "selling_tail_len": float(sell_tail),
        "profile_shape": float(_shape(bins, lo, hi, previous_poc_index)),
        "ledge_up": up_price,
        "ledge_down": down_price,
        "bull_poc": bottom + (int(np.argmax(bull)) + 0.5) * width
        if np.max(bull) > 0
        else 0.0,
        "bear_poc": bottom + (int(np.argmax(bear)) + 0.5) * width
        if np.max(bear) > 0
        else 0.0,
        "total_volume": total,
        "total_bull_volume": bull_total,
        "total_bear_volume": bear_total,
    }, int(np.argmax(bins))
