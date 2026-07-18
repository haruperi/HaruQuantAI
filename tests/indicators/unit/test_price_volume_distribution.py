"""Unit tests for rolling price-volume distribution."""

import pytest
from app.services.indicators.volume import price_volume_distribution

from tests.indicators.helpers import build_dataset


def test_price_volume_distribution_returns_dominant_bin_center() -> None:
    """FR-INDI-030: the highest-volume price bin determines the POC."""
    data = build_dataset([(0.5, 2.0, 0.0, 0.5, 10.0), (1.5, 2.0, 0.0, 1.5, 20.0)])
    result = price_volume_distribution(data, period=2, bins=2)
    assert result.values["price_volume_distribution_2_2"].iloc[-1] == pytest.approx(1.5)
