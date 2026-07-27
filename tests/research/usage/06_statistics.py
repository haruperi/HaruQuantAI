"""Executable Research statistics usage example.

Demonstrates block bootstrap resampling, permutation tests, null model
generation, null summaries, and multiple testing corrections.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research import StatisticalConfig
from app.services.research.statistics import (
    benjamini_hochberg,
    block_bootstrap_ci,
    block_bootstrap_distribution,
    compute_null_percentile,
    exceeds_null_threshold,
    holm_bonferroni,
    null_distribution_stats,
    permutation_test,
    r_space_null,
    random_entry_null,
    session_randomized_null,
    shuffle_returns_null,
)


def _config() -> StatisticalConfig:
    """Build seeded and bounded statistical settings.

    Returns:
        A validated statistical configuration instance.
    """
    return StatisticalConfig(7, 20, 20, 2, 20, "benjamini_hochberg")


def fr_res_050() -> None:
    """FR-RES-050.

    Generate a seeded stationary block-bootstrap distribution of a declared
    statistic.
    """
    data = np.arange(10.0)
    dist = block_bootstrap_distribution(data, statistic=np.mean, config=_config())
    print(f"FR-RES-050 distribution_size={dist.size}")


def fr_res_051() -> None:
    """FR-RES-051.

    Return a lower and upper percentile confidence interval from the seeded
    bootstrap distribution.
    """
    interval = block_bootstrap_ci(
        np.arange(10.0), statistic=np.mean, confidence=0.95, config=_config()
    )
    print(f"FR-RES-051 interval={interval}")


def fr_res_052() -> None:
    """FR-RES-052.

    Compute a one-sided or two-sided permutation p-value against a seeded null.
    """
    p_value = permutation_test(
        1.0, np.arange(5.0), alternative="upper", config=_config()
    )
    print(f"FR-RES-052 p_value={p_value}")


def fr_res_053() -> None:
    """FR-RES-053.

    Generate a seeded random-entry null distribution matched to declared side,
    horizon, and sample.
    """
    df = pd.DataFrame({"close": np.arange(1.0, 21.0)})
    result = random_entry_null(df, side="buy", hold_bars=2, config=_config())
    print(f"FR-RES-053 null_size={result.size}")


def fr_res_054() -> None:
    """FR-RES-054.

    Generate a seeded null distribution in R-multiple space from declared
    trade assumptions.
    """
    result = r_space_null(np.asarray([-1.0, 1.0]), config=_config())
    print(f"FR-RES-054 null_size={result.size}")


def fr_res_055() -> None:
    """FR-RES-055.

    Generate a seeded null by shuffling entries only within the same configured
    session.
    """
    # session_randomized_null requires a finite log_return column plus tags.
    df = pd.DataFrame({"log_return": range(20), "session": ["A"] * 10 + ["B"] * 10})
    result = session_randomized_null(df, session_column="session", config=_config())
    print(f"FR-RES-055 null_size={result.size}")


def fr_res_056() -> None:
    """FR-RES-056.

    Generate a seeded null by shuffling return blocks while preserving declared
    block length.
    """
    result = shuffle_returns_null(
        pd.Series([0.01, -0.02, 0.03, -0.01, 0.02]), config=_config()
    )
    print(f"FR-RES-056 null_size={result.size}")


def fr_res_057() -> None:
    """FR-RES-057.

    Compute the observed percentile within a finite non-empty null
    distribution.
    """
    percentile = compute_null_percentile(0.5, np.arange(-1.0, 1.0, 0.1))
    print(f"FR-RES-057 percentile={percentile}")


def fr_res_058() -> None:
    """FR-RES-058.

    Return finite count, location, dispersion, and declared quantiles for a
    null distribution.
    """
    stats = null_distribution_stats(np.arange(-1.0, 1.0, 0.1))
    print(f"FR-RES-058 keys={sorted(stats.keys())}")


def fr_res_059() -> None:
    """FR-RES-059.

    Determine threshold exceedance under an explicit upper/lower/two-sided
    rule.
    """
    exceeds = exceeds_null_threshold(
        0.9, np.arange(-1.0, 1.0, 0.1), quantile=0.95, alternative="upper"
    )
    print(f"FR-RES-059 exceeds={exceeds}")


def fr_res_060() -> None:
    """FR-RES-060.

    Apply Benjamini-Hochberg FDR correction to finite p-values in original
    order.
    """
    adjusted = benjamini_hochberg((0.01, 0.04, 0.20), q=0.05)
    print(f"FR-RES-060 adjusted_p_values={adjusted}")


def fr_res_061() -> None:
    """FR-RES-061.

    Apply Holm-Bonferroni family-wise correction to finite p-values in
    original order.
    """
    adjusted = holm_bonferroni((0.01, 0.04, 0.20), alpha=0.05)
    print(f"FR-RES-061 adjusted_p_values={adjusted}")


def main() -> None:
    """Run every Research statistics requirement demonstration in order."""
    print("=" * 80)
    print("Research Example 6: Resampling, Null Models, and Corrections")
    print("=" * 80)
    fr_res_050()
    fr_res_051()
    fr_res_052()
    fr_res_053()
    fr_res_054()
    fr_res_055()
    fr_res_056()
    fr_res_057()
    fr_res_058()
    fr_res_059()
    fr_res_060()
    fr_res_061()


if __name__ == "__main__":
    main()
