"""Runnable usage examples for Research feature calculations."""

import numpy as np
import pandas as pd
from app.services.research.contracts import (
    DataQualityReport,
    FeatureConfig,
    PreparedDataset,
    ResearchResourceLimits,
)
from app.services.research.features import (
    build_research_feature_frame,
    forward_max_adverse_excursion,
    forward_max_favorable_excursion,
    forward_returns,
    hurst_exponent,
    log_returns,
    rolling_hurst,
    simple_returns,
)
from app.utils import logger

_HASH = "d" * 64


def _prices() -> pd.Series:
    """Build usage prices.

    Returns:
        Positive UTC-indexed prices.
    """
    logger.debug("Building Research feature usage prices")
    return pd.Series(
        np.linspace(100.0, 130.0, 40),
        index=pd.date_range("2026-01-01", periods=40, freq="h", tz="UTC"),
    )


def _frame() -> pd.DataFrame:
    """Build usage OHLCVS frame.

    Returns:
        UTC-indexed analytical frame.
    """
    logger.debug("Building Research feature usage frame")
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


def test_usage_calculations_log_returns() -> None:
    """Compute aligned log returns."""
    logger.debug("Running log-return usage")
    assert len(log_returns(_prices())) == 40


def test_usage_calculations_simple_returns() -> None:
    """Compute aligned arithmetic returns."""
    logger.debug("Running simple-return usage")
    assert len(simple_returns(_prices())) == 40


def test_usage_calculations_hurst_exponent() -> None:
    """Estimate one Hurst exponent."""
    logger.debug("Running Hurst usage")
    assert np.isfinite(hurst_exponent(_prices(), minimum_samples=20))


def test_usage_calculations_rolling_hurst() -> None:
    """Compute rolling Hurst evidence."""
    logger.debug("Running rolling-Hurst usage")
    assert rolling_hurst(_prices(), window=20, minimum_samples=20).notna().any()


def test_usage_calculations_forward_returns() -> None:
    """Compute research-only forward returns."""
    logger.debug("Running forward-return usage")
    assert forward_returns(_prices(), horizon=2, mode="log", output_label="f2").attrs[
        "research_only"
    ]


def test_usage_calculations_forward_mfe() -> None:
    """Compute buy-side favorable excursion."""
    logger.debug("Running favorable-excursion usage")
    assert (
        forward_max_favorable_excursion(_frame(), horizon=2, side="buy").notna().any()
    )


def test_usage_calculations_forward_mae() -> None:
    """Compute buy-side adverse excursion."""
    logger.debug("Running adverse-excursion usage")
    assert forward_max_adverse_excursion(_frame(), horizon=2, side="buy").notna().any()


def test_usage_frame_build_research_feature_frame() -> None:
    """Build a lineage-bearing feature frame."""
    logger.debug("Running Research feature-frame usage")
    prepared = PreparedDataset(
        _frame(),
        "v1",
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )
    frame, metadata = build_research_feature_frame(
        prepared,
        indicator_results={},
        config=FeatureConfig({"hurst": 20}, (2,), (), "preserve"),
        limits=ResearchResourceLimits(100, 10.0, 1024),
    )
    assert len(frame) == 40
    assert metadata["schema_version"] == "v1"
