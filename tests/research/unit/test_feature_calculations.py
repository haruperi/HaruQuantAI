"""Unit tests for Research-owned feature calculations."""

import numpy as np
import pandas as pd
import pytest
from app.services.research.features import (
    forward_max_adverse_excursion,
    forward_max_favorable_excursion,
    forward_returns,
    hurst_exponent,
    log_returns,
    rolling_hurst,
    simple_returns,
)
from app.utils import logger
from app.utils.errors import ValidationError


def _prices(count: int = 40) -> pd.Series:
    """Build deterministic positive prices.

    Args:
        count: Number of prices.

    Returns:
        UTC-indexed price series.
    """
    logger.debug("Building Research feature test prices")
    return pd.Series(
        np.linspace(100.0, 120.0, count),
        index=pd.date_range("2026-01-01", periods=count, freq="h", tz="UTC"),
    )


def _ohlc() -> pd.DataFrame:
    """Build deterministic OHLC evidence.

    Returns:
        OHLC frame.
    """
    logger.debug("Building Research excursion test frame")
    close = _prices(6)
    return pd.DataFrame({"high": close + 1.0, "low": close - 1.0, "close": close})


def test_log_returns_preserves_alignment() -> None:
    """Verify log returns preserve the exact index."""
    logger.debug("Testing Research log-return alignment")
    prices = _prices()
    result = log_returns(prices)
    assert result.index.equals(prices.index)
    assert pd.isna(result.iloc[0])


def test_simple_returns_constant_series() -> None:
    """Verify constant prices produce zero arithmetic returns after warm-up."""
    logger.debug("Testing Research constant simple returns")
    result = simple_returns(pd.Series([2.0, 2.0, 2.0]))
    assert result.iloc[1:].eq(0.0).all()


def test_hurst_rejects_insufficient_sample() -> None:
    """Verify Hurst estimation rejects undersized samples."""
    logger.debug("Testing Research Hurst sample policy")
    with pytest.raises(ValidationError):
        hurst_exponent(_prices(10), minimum_samples=20)


def test_rolling_hurst_has_declared_warmup() -> None:
    """Verify rolling Hurst emits warm-up NaNs."""
    logger.debug("Testing Research rolling-Hurst warm-up")
    result = rolling_hurst(_prices(), window=20, minimum_samples=20)
    assert result.iloc[:19].isna().all()


def test_forward_returns_never_used_as_feature() -> None:
    """Verify forward returns carry research-only metadata."""
    logger.debug("Testing Research forward-return classification")
    result = forward_returns(_prices(), horizon=2, mode="log", output_label="forward_2")
    assert result.attrs["research_only"] is True
    assert result.iloc[-2:].isna().all()


def test_forward_mfe_buy_sell_direction() -> None:
    """Verify buy and sell favorable excursions use opposite extremes."""
    logger.debug("Testing Research favorable excursion direction")
    buy = forward_max_favorable_excursion(_ohlc(), horizon=2, side="buy")
    sell = forward_max_favorable_excursion(_ohlc(), horizon=2, side="sell")
    assert buy.iloc[0] > 0
    assert sell.iloc[0] < 0


def test_forward_mae_buy_sell_direction() -> None:
    """Verify adverse excursions are direction-aware."""
    logger.debug("Testing Research adverse excursion direction")
    buy = forward_max_adverse_excursion(_ohlc(), horizon=2, side="buy")
    sell = forward_max_adverse_excursion(_ohlc(), horizon=2, side="sell")
    assert buy.iloc[0] > 0
    assert sell.iloc[0] < 0
