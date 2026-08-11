"""Standalone usage evidence for FEAT-INDI-12."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import build_chart_pattern_evidence
from tests.indicators.usage._migration_support import run_requirement

_COMMON = {"left": 1, "right": 1, "atr_period": 3}


def fr_indi_031() -> None:
    """FR-INDI-031: Demonstrate doji evidence."""
    run_requirement("FR-INDI-031", "doji", {"threshold": 0.1})


def fr_indi_032() -> None:
    """FR-INDI-032: Demonstrate two-bar engulfing evidence."""
    run_requirement("FR-INDI-032", "engulfing", {})


def fr_indi_033() -> None:
    """FR-INDI-033: Demonstrate pinbar evidence."""
    run_requirement("FR-INDI-033", "pinbar", {})


def fr_indi_034() -> None:
    """FR-INDI-034: Demonstrate inside-bar containment evidence."""
    run_requirement("FR-INDI-034", "inside_bar", {})


def fr_indi_077() -> None:
    """FR-INDI-077: Demonstrate double-top/double-bottom evidence."""
    run_requirement(
        "FR-INDI-077",
        "double_top_bottom",
        _COMMON
        | {"tau_price": 0.05, "d_min_atr": 0.1, "beta_atr": 0.0, "m_confirm": 5},
    )


def fr_indi_078() -> None:
    """FR-INDI-078: Demonstrate head-and-shoulders evidence."""
    run_requirement(
        "FR-INDI-078",
        "head_and_shoulders",
        _COMMON
        | {"tau_shoulder": 0.1, "d_head_atr": 0.1, "beta_atr": 0.0, "m_confirm": 5},
    )


def fr_indi_079() -> None:
    """FR-INDI-079: Demonstrate triangle evidence."""
    run_requirement(
        "FR-INDI-079",
        "triangle",
        _COMMON
        | {"lookback": 10, "min_touches": 2, "slope_flat": 0.01, "beta_atr": 0.0},
    )


def fr_indi_080() -> None:
    """FR-INDI-080: Demonstrate flag/pennant evidence."""
    run_requirement(
        "FR-INDI-080",
        "flag_pennant",
        {
            "atr_period": 3,
            "impulse_lookback": 3,
            "consolidation_bars": 3,
            "impulse_min_atr": 0.1,
            "retrace_max": 1.0,
            "beta_atr": 0.0,
        },
    )


def fr_indi_081() -> None:
    """FR-INDI-081: Demonstrate breakout/retest evidence."""
    run_requirement(
        "FR-INDI-081",
        "breakout_retest",
        _COMMON | {"beta_atr": 0.0, "tau_price": 1.0, "m": 5},
    )


def fr_indi_082() -> None:
    """FR-INDI-082: Demonstrate wedge evidence."""
    run_requirement(
        "FR-INDI-082",
        "wedge",
        _COMMON | {"lookback": 10, "min_touches": 2, "beta_atr": 0.0},
    )


def fr_indi_083() -> None:
    """FR-INDI-083: Demonstrate rectangle evidence."""
    run_requirement(
        "FR-INDI-083",
        "rectangle",
        _COMMON
        | {
            "lookback": 10,
            "min_touches": 2,
            "slope_flat": 1.0,
            "tolerance": 1.0,
            "beta_atr": 0.0,
        },
    )


def fr_indi_084() -> None:
    """FR-INDI-084: Demonstrate three-bar reversal evidence."""
    run_requirement(
        "FR-INDI-084",
        "three_bar_reversal",
        {"atr_period": 3, "body_min_atr": 0.1, "confirm_fraction": 0.5},
    )


def main() -> None:
    """Exercise the new Pattern public operations."""
    fr_indi_031()
    fr_indi_032()
    fr_indi_033()
    fr_indi_034()
    fr_indi_077()
    fr_indi_078()
    fr_indi_079()
    fr_indi_080()
    fr_indi_081()
    fr_indi_082()
    fr_indi_083()
    fr_indi_084()
    evidence = build_chart_pattern_evidence(
        {"doji": 1, "engulfing": 0},
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    print(f"\nStatus: {evidence.status}")
    print(f"\nMessage: {evidence.message}")
    print(f"\nData: {evidence.data}")


if __name__ == "__main__":
    main()
