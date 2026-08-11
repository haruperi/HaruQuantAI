"""Standalone usage evidence for FEAT-INDI-10."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.indicators.usage._migration_support import run_requirement


def fr_indi_070() -> None:
    """FR-INDI-070: Demonstrate ADX/DMI regime evidence."""
    run_requirement(
        "FR-INDI-070",
        "adx_dmi_regime",
        {"period": 3, "adx_trend": 25.0, "adx_range": 20.0},
    )


def fr_indi_071() -> None:
    """FR-INDI-071: Demonstrate choppiness regime evidence."""
    run_requirement(
        "FR-INDI-071",
        "choppiness_regime",
        {"period": 3, "lower_threshold": 38.2, "upper_threshold": 61.8},
    )


def fr_indi_072() -> None:
    """FR-INDI-072: Demonstrate Hurst regime evidence."""
    run_requirement(
        "FR-INDI-072",
        "hurst_regime",
        {
            "window": 16,
            "min_scale": 2,
            "max_scale": 8,
            "scale_count": 3,
            "lower_threshold": 0.45,
            "upper_threshold": 0.55,
        },
    )


def fr_indi_073() -> None:
    """FR-INDI-073: Demonstrate Donchian breakout regime evidence."""
    run_requirement(
        "FR-INDI-073",
        "donchian_breakout_regime",
        {"period": 3, "atr_period": 3, "beta_atr": 0.0},
    )


def fr_indi_074() -> None:
    """FR-INDI-074: Demonstrate volatility/liquidity stress evidence."""
    run_requirement(
        "FR-INDI-074",
        "volatility_liquidity_stress_regime",
        {
            "vol_reference_period": 5,
            "vol_period": 3,
            "amihud_window": 3,
            "p_vol_extreme": 0.8,
            "p_illiquidity_extreme": 0.8,
            "p_illiquidity_high": 0.6,
        },
    )


def fr_indi_075() -> None:
    """FR-INDI-075: Demonstrate final descriptive regime resolution."""
    run_requirement(
        "FR-INDI-075",
        "final_regime_resolver",
        {
            "adx_period": 3,
            "adx_trend": 25.0,
            "adx_range": 20.0,
            "chop_period": 3,
            "chop_lower_threshold": 38.2,
            "chop_upper_threshold": 61.8,
            "donchian_period": 3,
            "atr_period": 3,
            "beta_atr": 0.0,
            "vol_reference_period": 5,
            "vol_period": 3,
            "amihud_window": 3,
            "p_vol_extreme": 0.8,
            "p_illiquidity_extreme": 0.8,
            "p_illiquidity_high": 0.6,
        },
    )


def main() -> None:
    """Exercise every Regime public operation."""
    fr_indi_070()
    fr_indi_071()
    fr_indi_072()
    fr_indi_073()
    fr_indi_074()
    fr_indi_075()


if __name__ == "__main__":
    main()
