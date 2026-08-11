"""Unit tests for the official price-gap and fair-value-gap calculator."""

import pytest
from app.services.indicators import gaps

from tests.indicators.helpers import (
    assert_error,
    build_dataset,
    result_values,
    unwrap_response,
)

_BARS = [
    (9.0, 9.5, 8.5, 9.0, 100.0),
    (10.0, 10.5, 9.5, 10.0, 100.0),
    (11.5, 12.0, 11.2, 11.8, 100.0),
    (12.2, 12.5, 12.1, 12.3, 100.0),
]


def test_gaps_detects_a_one_bar_gap_up() -> None:
    """A clean gap up between consecutive bars reports its size at the row.

    All four output columns (``gap_up``, ``gap_down``, ``fvg_up``,
    ``fvg_down``) share one row-level validity mask (the 3-bar FVG
    dependency), so the first row at which any gap can be reported is row
    index two.
    """
    data = build_dataset(_BARS)
    result = unwrap_response(gaps(data, min_gap=0.1))
    values = result_values(result)
    assert values["gap_up"].iloc[2] == pytest.approx(11.2 - 10.5)
    assert values["gap_down"].iloc[2] == 0.0


def test_gaps_first_rows_are_warmup() -> None:
    """The first two rows have no confirmed 3-bar window and stay unavailable."""
    data = build_dataset(_BARS)
    result = unwrap_response(gaps(data, min_gap=0.1))
    values = result_values(result)
    assert values["gap_up"].iloc[:2].isna().all()
    assert (values["unavailable_reason"].iloc[:2] == "warmup").all()


def test_gaps_rejects_negative_min_gap() -> None:
    """A negative minimum gap threshold is rejected before calculation."""
    data = build_dataset(_BARS)
    assert_error(gaps(data, min_gap=-1.0), "IND_INVALID_PARAMETER")


def test_gaps_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(gaps(data, min_gap=0.1))
    second = unwrap_response(gaps(data, min_gap=0.1))
    assert result_values(first)["gap_up"].tolist() == pytest.approx(
        result_values(second)["gap_up"].tolist(), nan_ok=True
    )
