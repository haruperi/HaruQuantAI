"""Unit tests for Stochastic indicator and composition signals with full donor options."""

from __future__ import annotations

import numpy as np
import pytest
from app.extend.blocks.indicators.momentum.stochastic import (
    MA_EMA,
    MA_LWMA,
    MA_SMA,
    MA_SMMA,
    PRICE_CLOSE_CLOSE,
    PRICE_LOW_HIGH,
    Stochastic,
)
from app.extend.blocks.registry import BlockRegistry, BlockRegistryError
from app.extend.blocks.series import BarData
from pydantic import ValidationError


@pytest.fixture
def sample_bars() -> BarData:
    """Deterministic OHLC sample dataset."""
    high = np.array([10.0, 11.0, 12.0, 11.5, 13.0, 12.5, 14.0, 15.0, 14.5, 16.0])
    low = np.array([9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 13.0, 12.5, 13.5])
    close = np.array([9.5, 10.5, 11.0, 11.0, 12.0, 12.0, 13.5, 14.0, 13.0, 15.5])
    return BarData.from_arrays(high=high, low=low, close=close)


def test_stochastic_parameter_validation() -> None:
    """Verify stochastic configuration bounds on MA method and price field."""
    # Valid configurations
    st = Stochastic(ma_method=MA_SMA, price_field=PRICE_LOW_HIGH)
    assert st.ma_method == 0
    assert st.price_field == 0

    st_close = Stochastic(ma_method=MA_LWMA, price_field=PRICE_CLOSE_CLOSE)
    assert st_close.ma_method == 3
    assert st_close.price_field == 1

    # Invalid configurations
    with pytest.raises(ValidationError):
        Stochastic(ma_method=4)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Stochastic(ma_method=-1)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Stochastic(price_field=2)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Stochastic(price_field=-1)  # type: ignore[call-arg]


def test_stochastic_required_inputs_conditioned_on_price_field(
    sample_bars: BarData,
) -> None:
    """Verify market dependencies adapt when price_field=1 (Close/Close)."""
    st_hl = Stochastic(price_field=PRICE_LOW_HIGH)
    assert st_hl.required_inputs() == ("high", "low", "close")

    st_cc = Stochastic(price_field=PRICE_CLOSE_CLOSE)
    assert st_cc.required_inputs() == ("close",)

    # Executing close-only dataset succeeds when price_field=PRICE_CLOSE_CLOSE
    close_only_bars = BarData.from_arrays(close=sample_bars.close)
    res = st_cc.calculate(close_only_bars)
    assert "k" in res and "d" in res
    assert len(res["k"]) == len(sample_bars.close)


@pytest.mark.parametrize("ma_method", [MA_SMA, MA_EMA, MA_SMMA, MA_LWMA])
@pytest.mark.parametrize("price_field", [PRICE_LOW_HIGH, PRICE_CLOSE_CLOSE])
def test_stochastic_all_methods_and_selectors_calculate(
    sample_bars: BarData, ma_method: int, price_field: int
) -> None:
    """Execute Stochastic across all 4 MA methods and both price field options."""
    st = Stochastic(
        k_period=5,
        d_period=3,
        slowing=3,
        ma_method=ma_method,
        price_field=price_field,
    )
    result = st.calculate(sample_bars)
    assert "k" in result and "d" in result

    k_vals = result["k"].values
    d_vals = result["d"].values
    assert len(k_vals) == len(sample_bars.close)
    assert len(d_vals) == len(sample_bars.close)

    # Values in valid range or NaN
    valid_k = k_vals[~np.isnan(k_vals)]
    valid_d = d_vals[~np.isnan(d_vals)]
    assert len(valid_k) > 0
    assert len(valid_d) > 0
    assert np.all(valid_k >= 0.0) and np.all(valid_k <= 100.0)
    assert np.all(valid_d >= 0.0) and np.all(valid_d <= 100.0)


def test_stochastic_compositions_support_all_ma_and_price_fields(
    sample_bars: BarData,
) -> None:
    """Verify registry compositions execute properly with custom MA and price field."""
    registry = BlockRegistry()
    registry.discover("app/extend/blocks", authorized_root="app/extend")
    catalog = registry.snapshot()

    desc = catalog.require("signal.stochastic.stoch_slow_d_rising")
    # All 4 MA methods instantiate cleanly
    for ma in (0, 1, 2, 3):
        for pf in (0, 1):
            sig = desc.instantiate(
                k_period=5, d_period=3, slowing=3, ma_method=ma, price_field=pf
            )
            res = sig(bars=sample_bars)
            assert isinstance(res, bool)

    # Reject out-of-bounds
    with pytest.raises(BlockRegistryError):
        desc.instantiate(ma_method=5)
    with pytest.raises(BlockRegistryError):
        desc.instantiate(price_field=2)
