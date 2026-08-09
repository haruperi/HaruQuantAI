from app.services.indicators import measure_volatility_envelope


def test_volatility_envelope_uses_explicit_thresholds() -> None:
    result = measure_volatility_envelope(
        current=3.0,
        historical=1.0,
        operating_ratio=1.5,
        extreme_ratio=2.5,
    )
    assert result.data == {"ratio": 3.0, "state": "EXTREME", "extreme": True}
