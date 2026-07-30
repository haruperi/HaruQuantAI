"""Unit tests for the Inside Bar pattern."""

import pandas as pd
from app.services.indicators import inside_bar

from tests.indicators.helpers import build_dataset, result_values, unwrap_response


def test_inside_bar_matches_containment_fixture_with_warmup() -> None:
    """FR-INDI-034: exact range containment emits one after warmup."""
    data = build_dataset([(5, 10, 0, 5, 10), (5, 8, 2, 5, 10), (5, 9, 1, 5, 10)])
    values = result_values(unwrap_response(inside_bar(data)))["inside_bar"]
    assert pd.isna(values.iloc[0])
    assert values.iloc[1:].tolist() == [1.0, 0.0]
