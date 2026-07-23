"""Executable Research features usage example.

Demonstrates log returns, simple returns, Hurst exponent estimation, forward returns, and excursion features.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research.features import (
    forward_max_adverse_excursion,
    forward_max_favorable_excursion,
    forward_returns,
    hurst_exponent,
    log_returns,
    rolling_hurst,
    simple_returns,
)


def _prices() -> pd.Series:
    """Build positive UTC-indexed prices."""
    return pd.Series(
        np.linspace(100.0, 130.0, 40),
        index=pd.date_range("2026-01-01", periods=40, freq="h", tz="UTC"),
    )


def _frame() -> pd.DataFrame:
    """Build OHLCV frame."""
    close = _prices()
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 100.0,
            "spread": 0.1,
        }
    )


def example_features() -> None:
    """Demonstrate research feature calculations."""
    print("=" * 80)
    print("Research Example 3: Feature Calculations and Excursions")
    print("=" * 80)

    prices = _prices()
    frame = _frame()

    # 1. Returns calculation
    l_returns = log_returns(prices)
    s_returns = simple_returns(prices)
    print(
        f"Log returns count: {len(l_returns)}, Simple returns count: {len(s_returns)}"
    )

    # 2. Hurst exponent
    h_exp = hurst_exponent(prices, minimum_samples=20)
    print(f"Hurst exponent: {h_exp:.4f}")

    r_h = rolling_hurst(prices, window=20, minimum_samples=20)
    print(f"Rolling Hurst non-NaN values count: {r_h.notna().sum()}")

    # 3. Forward returns
    f_ret = forward_returns(prices, horizon=2, mode="log", output_label="f2")
    print(
        f"Forward returns output label: {f_ret.name}, research_only attr: {f_ret.attrs['research_only']}"
    )

    # 4. Excursions
    mfe = forward_max_favorable_excursion(frame, horizon=2, side="buy")
    mae = forward_max_adverse_excursion(frame, horizon=2, side="buy")
    print(f"Max Favorable Excursion (MFE) valid count: {mfe.notna().sum()}")
    print(f"Max Adverse Excursion (MAE) valid count: {mae.notna().sum()}")


def main() -> None:
    """Run Research features usage example."""
    example_features()


if __name__ == "__main__":
    main()
