"""Executable Research statistics usage example.

Demonstrates block bootstrap resampling, permutation tests, null model generation, and multiple testing corrections.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research.contracts import StatisticalConfig
from app.services.research.statistics import (
    benjamini_hochberg,
    block_bootstrap_ci,
    block_bootstrap_distribution,
    permutation_test,
    r_space_null,
    random_entry_null,
    shuffle_returns_null,
)


def _config() -> StatisticalConfig:
    """Build statistical settings."""
    return StatisticalConfig(7, 20, 20, 2, 20, "benjamini_hochberg")


def example_statistics() -> None:
    """Demonstrate research statistical methods."""
    print("=" * 80)
    print("Research Example 6: Resampling, Null Models, and Multiple Testing")
    print("=" * 80)

    cfg = _config()
    data = np.arange(10.0)

    # 1. Block bootstrap distribution & confidence intervals
    dist = block_bootstrap_distribution(data, statistic=np.mean, config=cfg)
    print(f"Block bootstrap distribution size: {dist.size}")

    lower, upper = block_bootstrap_ci(
        data, statistic=np.mean, confidence=0.95, config=cfg
    )
    print(f"Bootstrap 95% CI: [{lower:.4f}, {upper:.4f}]")

    # 2. Permutation test
    p_val = permutation_test(1.0, np.arange(5.0), alternative="upper", config=cfg)
    print(f"Permutation p-value: {p_val:.4f}")

    # 3. Null models
    df_prices = pd.DataFrame({"close": np.arange(1.0, 21.0)})
    re_null = random_entry_null(df_prices, side="buy", hold_bars=2, config=cfg)
    print(f"Random entry null size: {re_null.size}")

    r_null = r_space_null(np.asarray([-1.0, 1.0]), config=cfg)
    print(f"R-space null size: {r_null.size}")

    shuf_null = shuffle_returns_null(np.asarray([-0.01, 0.02, 0.01]), config=cfg)
    print(f"Shuffle returns null size: {shuf_null.size}")

    # 4. Multiple testing corrections
    p_values = (0.01, 0.04, 0.20)
    bh_rejections = benjamini_hochberg(p_values, q=0.05)
    print(f"Benjamini-Hochberg rejections for p-values {p_values}: {bh_rejections}")


def main() -> None:
    """Run Research statistics usage example."""
    example_statistics()


if __name__ == "__main__":
    main()
