"""Component invariants for ADX/DMI regime classification."""

from tests.indicators.formula_invariants import assert_formula_invariants


def test_adx_dmi_regime_is_deterministic_and_causal() -> None:
    """Preserve historical ADX/DMI regimes under future extension."""
    assert_formula_invariants(
        "adx_dmi_regime", {"period": 3, "adx_trend": 25.0, "adx_range": 20.0}
    )
