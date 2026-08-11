"""Focused invariants for head-and-shoulders evidence."""

import numpy as np
from app.services.indicators.patterns.head_and_shoulders import _scan

from tests.indicators.formula_invariants import (
    assert_formula_invariants,
    oscillating_bars,
)


def test_head_and_shoulders_is_deterministic_and_causal() -> None:
    """Preserve confirmed three-pivot evidence under future extension."""
    assert_formula_invariants(
        "head_and_shoulders",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "tau_shoulder": 0.3,
            "d_head_atr": 0.1,
            "beta_atr": 0.0,
            "m_confirm": 5,
        },
        bars=oscillating_bars(),
    )


def test_scan_detects_and_confirms_bearish_formation() -> None:
    """Confirm a causal three-shoulder formation after neckline breakout."""
    shoulder_flag = np.array([1, 0, 1, 0, 1, 0, 0], dtype=float)
    shoulder_price = np.array([10, np.nan, 12, np.nan, 10, np.nan, np.nan])
    trough_flag = np.array([0, 1, 0, 1, 0, 0, 0], dtype=float)
    trough_price = np.array([np.nan, 8, np.nan, 8, np.nan, np.nan, np.nan])
    state = _scan(
        shoulder_flag=shoulder_flag,
        shoulder_price=shoulder_price,
        trough_flag=trough_flag,
        trough_price=trough_price,
        close=np.array([10, 9, 11, 9, 10, 9, 7], dtype=float),
        atr_values=np.ones(7),
        tau_shoulder=0.1,
        d_head_atr=1.0,
        beta_atr=0.0,
        m_confirm=3,
        first_valid=0,
        bearish=True,
    )
    assert state[4] == 1.0
    assert state[6] == 2.0
