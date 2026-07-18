"""Unit tests for On-Balance Volume."""

from app.services.indicators.volume import obv

from tests.indicators.helpers import build_dataset


def test_obv_matches_directional_cumulative_fixture() -> None:
    """FR-INDI-028: OBV adds, subtracts, or retains volume by close direction."""
    data = build_dataset(
        [
            (1, 1.5, 0.5, 1, 10),
            (2, 2.5, 1.5, 2, 20),
            (1, 1.5, 0.5, 1, 30),
            (1, 1.5, 0.5, 1, 40),
        ]
    )
    assert obv(data).values["obv"].tolist() == [0.0, 20.0, -10.0, -10.0]
