"""Unit tests for tick derivation contracts, provenance, and compiled kernel."""

import numpy as np
from app.services.data.tick_derivation._kernel import (
    _add_ratio_half_even,
    _phase_mask,
    generate_four_tick_arrays,
    generate_volume_tick_arrays,
)
from app.services.data.tick_derivation.contracts import SpreadModel, TickDerivationModel
from app.services.data.tick_derivation.provenance import DERIVED_TICK_SOURCE


def test_tick_derivation_provenance_and_contracts() -> None:
    """Verify tick derivation provenance constant and contract types."""
    assert DERIVED_TICK_SOURCE == "derived"
    model: TickDerivationModel = "real"
    spread: SpreadModel = "native_spread"
    assert model == "real"
    assert spread == "native_spread"


def test_add_ratio_half_even() -> None:
    """Test half-even rounding kernel logic directly."""
    # Exact: 10 + 5/2 = 12.5 -> rounds to 12 (even)
    assert _add_ratio_half_even(10, 5, 2) == 12
    # Exact: 11 + 5/2 = 13.5 -> rounds to 14 (even)
    assert _add_ratio_half_even(11, 5, 2) == 14
    # Negative ratio
    assert _add_ratio_half_even(10, -5, 2) == 8


def test_phase_mask() -> None:
    """Test phase mask calculation for local indices."""
    phases = np.array([1, 2, 4, 8], dtype=np.int64)
    # First tick (index 0)
    assert _phase_mask(0, 10, 3, 6, phases) == 1
    # Turn 1 (index 3)
    assert _phase_mask(3, 10, 3, 6, phases) == 2
    # Turn 2 (index 6)
    assert _phase_mask(6, 10, 3, 6, phases) == 4
    # Last tick (index 9)
    assert _phase_mask(9, 10, 3, 6, phases) == 8
    # Middle non-turn index (index 2)
    assert _phase_mask(2, 10, 3, 6, phases) == 0


def test_generate_four_tick_arrays() -> None:
    """Test generating 4-tick waypoint arrays."""
    waypoints = np.array([[100000, 100500, 99500, 100200]], dtype=np.int64)
    phases = np.array([[1, 2, 4, 8]], dtype=np.int64)
    bar_start_us = np.array([1700000000000000], dtype=np.int64)
    offsets_ms = np.array([0, 100, 200, 300], dtype=np.int64)
    spread_ticks = np.array([10], dtype=np.int64)
    output_divisor = 10

    ts, bids, asks, local_idx, output_phases, bar_idx = generate_four_tick_arrays(
        waypoints, phases, bar_start_us, offsets_ms, spread_ticks, output_divisor
    )

    assert len(ts) == 4
    assert bids[0] == 10000
    assert asks[0] == 10001
    assert list(local_idx) == [0, 1, 2, 3]
    assert list(output_phases) == [1, 2, 4, 8]
    assert list(bar_idx) == [0, 0, 0, 0]


def test_generate_volume_tick_arrays() -> None:
    """Test generating volume tick arrays."""
    waypoints = np.array([[100000, 100500, 99500, 100200]], dtype=np.int64)
    phases = np.array([1, 2, 4, 8], dtype=np.int64).reshape(1, 4)
    bar_start_us = np.array([1700000000000000], dtype=np.int64)
    tick_counts = np.array([5], dtype=np.int64)
    output_offsets = np.array([0, 5], dtype=np.int64)
    spread_ticks = np.array([10], dtype=np.int64)
    bar_ms = 300000
    output_divisor = 10

    ts, _bids, _asks, local_idx, _output_phases, bar_idx = generate_volume_tick_arrays(
        waypoints,
        phases,
        bar_start_us,
        tick_counts,
        output_offsets,
        spread_ticks,
        bar_ms,
        output_divisor,
    )

    assert len(ts) == 5
    assert list(local_idx) == [0, 1, 2, 3, 4]
    assert list(bar_idx) == [0, 0, 0, 0, 0]
