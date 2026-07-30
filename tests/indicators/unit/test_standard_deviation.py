"""Unit tests for rolling standard deviation."""

import pytest
from app.services.indicators import standard_deviation

from tests.indicators.helpers import close_dataset, result_values, unwrap_response


def test_standard_deviation_matches_sample_fixture() -> None:
    """FR-INDI-026: price dispersion uses sample standard deviation."""
    result = unwrap_response(
        standard_deviation(close_dataset([1.0, 2.0, 3.0]), period=3)
    )
    assert result_values(result)["standard_deviation_3"].iloc[-1] == pytest.approx(1.0)
