"""Executable Research features usage example.

Demonstrates log/simple returns, Hurst estimation, forward returns,
excursions, and canonical feature-frame assembly.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research import (
    build_research_feature_frame,
    create_research_value,
    forward_max_adverse_excursion,
    forward_max_favorable_excursion,
    forward_returns,
    hurst_exponent,
    log_returns,
    rolling_hurst,
    simple_returns,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _prices() -> pd.Series:
    """Build positive UTC-indexed close prices.

    Returns:
        Series of 40 linearly-spaced floats from 100 to 130 on an hourly
        UTC index.
    """
    return pd.Series(
        np.linspace(100.0, 130.0, 40),
        index=pd.date_range("2026-01-01", periods=40, freq="h", tz="UTC"),
    )


def _frame() -> pd.DataFrame:
    """Build a bounded OHLCV frame.

    Returns:
        OHLCV DataFrame built from :func:`_prices`.
    """
    close = _prices()
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 100.0,
        }
    )


def fr_res_031() -> None:
    """FR-RES-031.

    Compute one-period log returns without mutating input and preserve index
    alignment.
    """
    _header(
        "FR-RES-031. Compute one-period log returns without mutating input and preserve index alignment."
    )
    result = log_returns(_prices())
    print(f"FR-RES-031 log_return_rows={len(result)}")


def fr_res_032() -> None:
    """FR-RES-032.

    Compute arithmetic returns without mutating input and preserve index
    alignment.
    """
    _header(
        "FR-RES-032. Compute arithmetic returns without mutating input and preserve index alignment."
    )
    result = simple_returns(_prices())
    print(f"FR-RES-032 simple_return_rows={len(result)}")


def fr_res_033() -> None:
    """FR-RES-033.

    Estimate Hurst exponent with explicit minimum sample and finite-value
    validation.
    """
    _header(
        "FR-RES-033. Estimate Hurst exponent with explicit minimum sample and finite-value validation."
    )
    estimate = hurst_exponent(_prices(), minimum_samples=20)
    print(f"FR-RES-033 hurst={estimate:.4f}")


def fr_res_034() -> None:
    """FR-RES-034.

    Compute rolling Hurst values with documented warm-up NaNs and stable
    alignment.
    """
    _header(
        "FR-RES-034. Compute rolling Hurst values with documented warm-up NaNs and stable alignment."
    )
    rolling = rolling_hurst(_prices(), window=20, minimum_samples=20)
    print(f"FR-RES-034 rolling_hurst_valid={int(rolling.notna().sum())}")


def fr_res_035() -> None:
    """FR-RES-035.

    Compute one canonical horizon-aligned forward return in log or simple
    mode and mark it research-only.
    """
    _header(
        "FR-RES-035. Compute one canonical horizon-aligned forward return in log or simple mode and mark it research-only."
    )
    forward = forward_returns(_prices(), horizon=2, mode="log", output_label="f2")
    print(
        f"FR-RES-035 label={forward.name} "
        f"research_only={forward.attrs['research_only']}"
    )


def fr_res_036() -> None:
    """FR-RES-036.

    Compute forward maximum favorable excursion for declared side/horizon
    with trailing unavailability explicit.
    """
    _header(
        "FR-RES-036. Compute forward maximum favorable excursion for declared side/horizon with trailing unavailability explicit."
    )
    mfe = forward_max_favorable_excursion(_frame(), horizon=2, side="buy")
    print(f"FR-RES-036 mfe_valid={int(mfe.notna().sum())}")


def fr_res_037() -> None:
    """FR-RES-037.

    Compute forward maximum adverse excursion for declared side/horizon with
    trailing unavailability explicit.
    """
    _header(
        "FR-RES-037. Compute forward maximum adverse excursion for declared side/horizon with trailing unavailability explicit."
    )
    mae = forward_max_adverse_excursion(_frame(), horizon=2, side="buy")
    print(f"FR-RES-037 mae_valid={int(mae.notna().sum())}")


def fr_res_038() -> None:
    """FR-RES-038.

    Build a new feature frame with declared lineage, warm-up/NaN behavior,
    caller-supplied public IndicatorResult v1 inputs, research-only forward
    columns, and no input mutation.
    """
    _header(
        "FR-RES-038. Build a new feature frame with declared lineage, warm-up/NaN behavior, caller-supplied public IndicatorResult v1 inputs, research-only forward columns, and no input mutation."
    )
    quality = create_research_value("DataQualityReport", (), (), ("schema",), ())
    prepared = create_research_value(
        "PreparedDataset",
        data=_frame(),
        schema_version="v1",
        quality=quality,
        dataset_hash="e" * 64,
        configuration_hash="e" * 64,
        source_references=("fixture",),
    )
    features = create_research_value(
        "FeatureConfig",
        {"sma": 2},
        (1,),
        # Forward column must match the generated "forward_return_{horizon}".
        ("forward_return_1",),
        "preserve",
    )
    limits = create_research_value("ResearchResourceLimits", 100, 10.0, 1024)
    frame, _metadata = build_research_feature_frame(
        prepared, indicator_results={}, config=features, limits=limits
    )
    print(f"FR-RES-038 feature_columns={len(frame.columns)}")


def main() -> None:
    """Run every Research feature requirement demonstration in order."""
    print("Research Example 3: Feature Calculations and Excursions")
    fr_res_031()
    fr_res_032()
    fr_res_033()
    fr_res_034()
    fr_res_035()
    fr_res_036()
    fr_res_037()
    fr_res_038()


if __name__ == "__main__":
    main()
