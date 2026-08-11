"""Unit tests for the ADX/DMI regime classifier."""

from app.services.indicators import adx_dmi_regime

from tests.indicators.helpers import assert_error, build_dataset, unwrap_response


def _trending_bars(count: int = 50) -> list[tuple[float, float, float, float, float]]:
    """Build a strongly trending bar series."""
    return [
        (10.0 + i, 12.0 + i * 1.1, 9.5 + i, 11.5 + i * 1.05, 100.0)
        for i in range(count)
    ]


def test_adx_dmi_regime_calculates_classification() -> None:
    """adx_dmi_regime classifies trend direction and strength cleanly."""
    data = build_dataset(_trending_bars(50))
    result = unwrap_response(
        adx_dmi_regime(data, period=14, adx_trend=25.0, adx_range=20.0)
    )
    assert result.indicator_id == "adx_dmi_regime"
    assert any("regime" in col for col in result.values.columns)


def test_adx_dmi_regime_rejects_invalid_period() -> None:
    """Period less than 2 is rejected fail-fast."""
    data = build_dataset(_trending_bars(20))
    assert_error(
        adx_dmi_regime(data, period=1, adx_trend=25.0, adx_range=20.0),
        "IND_INVALID_PARAMETER",
    )
