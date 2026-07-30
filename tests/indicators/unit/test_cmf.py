"""Unit tests for Chaikin Money Flow."""

import pytest
from app.services.indicators import cmf

from tests.indicators.helpers import build_dataset, result_values, unwrap_response


def test_cmf_matches_money_flow_volume_fixture() -> None:
    """FR-INDI-027: CMF divides rolling money-flow volume by volume."""
    data = build_dataset(
        [
            (1.0, 2.0, 0.0, 2.0, 100.0),
            (1.0, 2.0, 0.0, 0.0, 100.0),
            (1.0, 2.0, 0.0, 1.0, 100.0),
        ]
    )
    result = unwrap_response(cmf(data, period=2))
    values = result_values(result)
    assert values["cmf_2"].iloc[1] == pytest.approx(0.0)
    assert values["cmf_2"].iloc[2] == pytest.approx(-0.5)
