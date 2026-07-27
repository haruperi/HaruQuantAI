"""Unit tests for tick_derivation/_kernel.py with NUMBA_DISABLE_JIT=1 for coverage."""

import os

import numpy as np

# Ensure numba JIT is disabled so coverage can trace line execution
os.environ["NUMBA_DISABLE_JIT"] = "1"

from app.services.data.tick_derivation._kernel import (
    _add_ratio_half_even,
    _phase_mask,
    _write_volume_bar,
    generate_four_tick_arrays,
    generate_volume_tick_arrays,
)


def test_add_ratio_half_even_func() -> None:
    """Test _add_ratio_half_even math and rounding."""
    func = getattr(_add_ratio_half_even, "pyfunc", _add_ratio_half_even)
    # 10 + 5/2 = 12.5 -> rounds ties-to-even to 12
    assert func(10, 5, 2) == 12
    # 10 + 7/2 = 13.5 -> rounds ties-to-even to 14
    assert func(10, 7, 2) == 14
    # Negative numerator
    assert func(10, -5, 2) == 8
    # Ties to even
    assert func(0, 1, 2) == 0
    assert func(0, 3, 2) == 2


def test_phase_mask_func() -> None:
    """Test _phase_mask logic."""
    func = getattr(_phase_mask, "pyfunc", _phase_mask)
    phases = np.array([1, 2, 4, 8], dtype=np.int64)

    assert func(0, 10, 3, 6, phases) == 1
    assert func(3, 10, 3, 6, phases) == 2
    assert func(6, 10, 3, 6, phases) == 4
    assert func(9, 10, 3, 6, phases) == 8
    assert func(4, 10, 3, 6, phases) == 0


def test_write_volume_bar_func() -> None:
    """Test _write_volume_bar logic."""
    func = getattr(_write_volume_bar, "pyfunc", _write_volume_bar)

    waypoints = np.array([[100, 105, 95, 102]], dtype=np.int64)
    phases = np.array([[1, 2, 4, 8]], dtype=np.int64)
    bar_start_us = np.array([1600000000000000], dtype=np.int64)
    tick_counts = np.array([4], dtype=np.int64)
    output_offsets = np.array([0, 4], dtype=np.int64)
    spread_ticks = np.array([2], dtype=np.int64)

    timestamps = np.zeros(4, dtype=np.int64)
    bids = np.zeros(4, dtype=np.int64)
    asks = np.zeros(4, dtype=np.int64)
    local_indices = np.zeros(4, dtype=np.int64)
    output_phases = np.zeros(4, dtype=np.int8)
    bar_indices = np.zeros(4, dtype=np.int64)

    func(
        0,
        waypoints,
        phases,
        bar_start_us,
        tick_counts,
        output_offsets,
        spread_ticks,
        60000,
        1,
        timestamps,
        bids,
        asks,
        local_indices,
        output_phases,
        bar_indices,
    )
    assert bids[0] == 100


def test_generate_volume_tick_arrays_func() -> None:
    """Test generate_volume_tick_arrays logic."""
    func = getattr(generate_volume_tick_arrays, "pyfunc", generate_volume_tick_arrays)

    waypoints = np.array([[1000, 1050, 950, 1020]], dtype=np.int64)
    phases = np.array([[1, 2, 4, 8]], dtype=np.int64)
    bar_start_us = np.array([1600000000000000], dtype=np.int64)
    tick_counts = np.array([4], dtype=np.int64)
    output_offsets = np.array([0, 4], dtype=np.int64)
    spread_ticks = np.array([20], dtype=np.int64)

    res = func(
        waypoints,
        phases,
        bar_start_us,
        tick_counts,
        output_offsets,
        spread_ticks,
        60000,
        10,
    )
    assert len(res) == 6


def test_generate_four_tick_arrays_func() -> None:
    """Test generate_four_tick_arrays logic."""
    func = getattr(generate_four_tick_arrays, "pyfunc", generate_four_tick_arrays)

    waypoints = np.array([[1000, 1050, 950, 1020]], dtype=np.int64)
    phases = np.array([[1, 2, 4, 8]], dtype=np.int64)
    bar_start_us = np.array([1600000000000000], dtype=np.int64)
    offsets_ms = np.array([0, 15000, 30000, 45000], dtype=np.int64)
    spread_ticks = np.array([20], dtype=np.int64)

    res = func(
        waypoints,
        phases,
        bar_start_us,
        offsets_ms,
        spread_ticks,
        10,
    )
    assert len(res) == 6
