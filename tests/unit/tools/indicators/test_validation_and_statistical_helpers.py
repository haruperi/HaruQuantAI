"""Unit tests for indicator validation and statistical helper branches."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pytest

from tools.indicators.statistical import (
    calculate_hurst_frame,
    calculate_hurst_value,
)
from tools.indicators.validation import (
    apply_warmup_policy,
    ensure_dataframe,
    require_columns,
    require_known_warmup_policy,
    require_positive_float,
    require_positive_int,
)


@dataclass
class DataFrameHolder:
    """Small DataFrame-like object used to cover adapter input."""

    df: pd.DataFrame


def test_ensure_dataframe_accepts_supported_inputs() -> None:
    records = [{"close": 1.0}, {"close": 2.0}]
    mapping = {"close": [1.0, 2.0]}
    holder = DataFrameHolder(pd.DataFrame(mapping))

    assert len(ensure_dataframe(records)) == 2
    assert len(ensure_dataframe(mapping)) == 2
    assert len(ensure_dataframe(holder)) == 2


def test_validation_helpers_reject_invalid_inputs() -> None:
    frame = pd.DataFrame({"close": [1.0, 2.0]})

    with pytest.raises(TypeError):
        ensure_dataframe("not-frame")
    with pytest.raises(ValueError):
        ensure_dataframe(pd.DataFrame())
    with pytest.raises(ValueError):
        require_columns(frame, ["open"])
    with pytest.raises(TypeError):
        require_positive_int(True, name="period")
    with pytest.raises(ValueError):
        require_positive_int(0, name="period")
    with pytest.raises(TypeError):
        require_positive_float("1.0", name="multiplier")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        require_positive_float(0.0, name="multiplier")
    with pytest.raises(ValueError):
        require_known_warmup_policy("unknown")


def test_apply_warmup_policy_drop_and_fill_errors() -> None:
    frame = pd.DataFrame({"value": [np.nan, 2.0, 3.0]})

    dropped = apply_warmup_policy(frame.copy(), "value", warmup_policy="drop")
    assert dropped["value"].to_list() == [2.0, 3.0]

    with pytest.raises(ValueError):
        apply_warmup_policy(frame.copy(), "value", warmup_policy="fill")


def test_hurst_value_calculates_for_long_positive_and_shifted_series() -> None:
    positive = np.linspace(1.0, 150.0, 150)
    shifted = np.linspace(-5.0, 25.0, 150)

    assert np.isfinite(calculate_hurst_value(positive, min_length=50))
    assert np.isfinite(calculate_hurst_value(shifted, min_length=50))


def test_hurst_frame_custom_output_and_warmup_drop() -> None:
    frame = pd.DataFrame({"close": np.linspace(1.0, 150.0, 150)})

    result = calculate_hurst_frame(
        frame,
        period=50,
        output_col="hurst_custom",
        warmup_policy="drop",
    )

    assert "hurst_custom" in result.columns
    assert len(result) < len(frame)
