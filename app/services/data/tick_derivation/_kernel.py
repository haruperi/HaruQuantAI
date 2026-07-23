"""Compiled fixed-point kernels for deterministic tick derivation.

The kernels in this module are private implementation details. Inputs are validated
and converted to integer price quanta by ``generator.py`` before these functions
run, so the compiled loops perform no I/O, logging, Decimal conversion, or policy
decisions.
"""

from __future__ import annotations

import numpy as np
from numba import njit, prange
from numpy.typing import NDArray

Int64Array = NDArray[np.int64]
Int8Array = NDArray[np.int8]


@njit(cache=True)  # type: ignore[untyped-decorator]
def _add_ratio_half_even(base_value: int, numerator: int, denominator: int) -> int:
    """Add an integer ratio to a base and round the result ties-to-even.

    Args:
        base_value: Exact integer component of the result.
        numerator: Signed integer numerator.
        denominator: Strictly positive integer denominator.

    Returns:
        The exactly rounded integer quotient.
    """
    sign = -1 if numerator < 0 else 1
    magnitude = -numerator if numerator < 0 else numerator
    quotient = magnitude // denominator
    remainder = magnitude % denominator
    result = base_value + (sign * quotient)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and result % 2 != 0):
        result += sign
    return result


@njit(cache=True)  # type: ignore[untyped-decorator]
def _phase_mask(
    local_index: int,
    tick_count: int,
    first_turn: int,
    second_turn: int,
    phase_values: Int64Array,
) -> int:
    """Return the combined waypoint flags for one local tick index."""
    phase = 0
    if local_index == 0:
        phase |= phase_values[0]
    if local_index == first_turn:
        phase |= phase_values[1]
    if local_index == second_turn:
        phase |= phase_values[2]
    if local_index == tick_count - 1:
        phase |= phase_values[3]
    return phase


@njit(cache=True)  # type: ignore[untyped-decorator]
def _write_volume_bar(
    bar_index: int,
    waypoints: Int64Array,
    phases: Int64Array,
    bar_start_us: Int64Array,
    tick_counts: Int64Array,
    output_offsets: Int64Array,
    spread_ticks: Int64Array,
    bar_milliseconds: int,
    output_divisor: int,
    timestamps_us: Int64Array,
    bids: Int64Array,
    asks: Int64Array,
    local_indices: Int64Array,
    output_phases: Int8Array,
    bar_indices: Int64Array,
) -> None:
    """Write one bar into its exclusive output-array partition."""
    tick_count = tick_counts[bar_index]
    output_start = output_offsets[bar_index]
    steps = tick_count - 1
    base = steps // 3
    remainder = steps % 3
    first_length = base + (1 if remainder > 0 else 0)
    second_length = base + (1 if remainder > 1 else 0)
    third_length = base
    first_turn = first_length
    second_turn = first_length + second_length

    for local_index in range(tick_count):
        output_index = output_start + local_index
        if local_index <= first_turn:
            segment_start = waypoints[bar_index, 0]
            segment_end = waypoints[bar_index, 1]
            segment_step = local_index
            segment_steps = max(first_length, 1)
        elif local_index <= second_turn:
            segment_start = waypoints[bar_index, 1]
            segment_end = waypoints[bar_index, 2]
            segment_step = local_index - first_turn
            segment_steps = max(second_length, 1)
        else:
            segment_start = waypoints[bar_index, 2]
            segment_end = waypoints[bar_index, 3]
            segment_step = local_index - second_turn
            segment_steps = max(third_length, 1)

        delta = segment_end - segment_start
        bid_base = segment_start // output_divisor
        bid_remainder = segment_start % output_divisor
        denominator = segment_steps * output_divisor
        bid = _add_ratio_half_even(
            bid_base,
            (bid_remainder * segment_steps) + (delta * segment_step),
            denominator,
        )
        ask_start = segment_start + spread_ticks[bar_index]
        ask_base = ask_start // output_divisor
        ask_remainder = ask_start % output_divisor
        ask = _add_ratio_half_even(
            ask_base,
            (ask_remainder * segment_steps) + (delta * segment_step),
            denominator,
        )
        phase = _phase_mask(
            local_index,
            tick_count,
            first_turn,
            second_turn,
            phases[bar_index],
        )

        raw_timestamp_us = (
            bar_start_us[bar_index]
            + ((bar_milliseconds * local_index) // tick_count) * 1_000
        )
        timestamps_us[output_index] = (raw_timestamp_us // 1_000_000) * 1_000_000
        bids[output_index] = bid
        asks[output_index] = ask
        local_indices[output_index] = local_index
        output_phases[output_index] = phase
        bar_indices[output_index] = bar_index


@njit(cache=True, parallel=True)  # type: ignore[untyped-decorator]
def generate_volume_tick_arrays(
    waypoints: Int64Array,
    phases: Int64Array,
    bar_start_us: Int64Array,
    tick_counts: Int64Array,
    output_offsets: Int64Array,
    spread_ticks: Int64Array,
    bar_milliseconds: int,
    output_divisor: int,
) -> tuple[Int64Array, Int64Array, Int64Array, Int64Array, Int8Array, Int64Array]:
    """Generate volume-sized tick columns in disjoint parallel bar partitions.

    Args:
        waypoints: Four fixed-point prices for every source bar.
        phases: Four phase flags matching each bar's waypoint order.
        bar_start_us: UTC epoch microseconds for every source bar.
        tick_counts: Output tick count for every source bar.
        output_offsets: Exclusive-prefix output offsets, including final total.
        spread_ticks: Fixed-point spread increment for every source bar.
        bar_milliseconds: Inferred duration of each bar in milliseconds.
        output_divisor: Internal fixed-point units per public output quantum.

    Returns:
        Timestamp, bid, ask, local-index, phase, and source-bar-index columns.
    """
    total = output_offsets[-1]
    timestamps_us = np.empty(total, dtype=np.int64)
    bids = np.empty(total, dtype=np.int64)
    asks = np.empty(total, dtype=np.int64)
    local_indices = np.empty(total, dtype=np.int64)
    output_phases = np.empty(total, dtype=np.int8)
    bar_indices = np.empty(total, dtype=np.int64)

    for bar_index in prange(tick_counts.size):
        _write_volume_bar(
            bar_index,
            waypoints,
            phases,
            bar_start_us,
            tick_counts,
            output_offsets,
            spread_ticks,
            bar_milliseconds,
            output_divisor,
            timestamps_us,
            bids,
            asks,
            local_indices,
            output_phases,
            bar_indices,
        )

    return (
        timestamps_us,
        bids,
        asks,
        local_indices,
        output_phases,
        bar_indices,
    )


@njit(cache=True, parallel=True)  # type: ignore[untyped-decorator]
def generate_four_tick_arrays(
    waypoints: Int64Array,
    phases: Int64Array,
    bar_start_us: Int64Array,
    offsets_ms: Int64Array,
    spread_ticks: Int64Array,
    output_divisor: int,
) -> tuple[Int64Array, Int64Array, Int64Array, Int64Array, Int8Array, Int64Array]:
    """Generate four canonical waypoint columns for every source bar.

    Args:
        waypoints: Four fixed-point prices for every source bar.
        phases: Four phase flags matching each bar's waypoint order.
        bar_start_us: UTC epoch microseconds for every source bar.
        offsets_ms: Four intra-bar timestamp offsets in milliseconds.
        spread_ticks: Fixed-point spread increment for every source bar.
        output_divisor: Internal fixed-point units per public output quantum.

    Returns:
        Timestamp, bid, ask, local-index, phase, and source-bar-index columns.
    """
    total = waypoints.shape[0] * 4
    timestamps_us = np.empty(total, dtype=np.int64)
    bids = np.empty(total, dtype=np.int64)
    asks = np.empty(total, dtype=np.int64)
    local_indices = np.empty(total, dtype=np.int64)
    output_phases = np.empty(total, dtype=np.int8)
    bar_indices = np.empty(total, dtype=np.int64)

    for bar_index in prange(waypoints.shape[0]):
        output_start = bar_index * 4
        for local_index in range(4):
            output_index = output_start + local_index
            raw_timestamp_us = bar_start_us[bar_index] + offsets_ms[local_index] * 1_000
            internal_bid = waypoints[bar_index, local_index]
            internal_ask = internal_bid + spread_ticks[bar_index]
            bid = _add_ratio_half_even(0, internal_bid, output_divisor)
            ask = _add_ratio_half_even(0, internal_ask, output_divisor)
            timestamps_us[output_index] = (raw_timestamp_us // 1_000_000) * 1_000_000
            bids[output_index] = bid
            asks[output_index] = ask
            local_indices[output_index] = local_index
            output_phases[output_index] = phases[bar_index, local_index]
            bar_indices[output_index] = bar_index

    return (
        timestamps_us,
        bids,
        asks,
        local_indices,
        output_phases,
        bar_indices,
    )


__all__ = ["generate_four_tick_arrays", "generate_volume_tick_arrays"]
