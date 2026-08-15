"""Provider-documented account-currency rounding tests."""

from decimal import Decimal

from app.services.simulator import convert_account_currency, unwrap_simulation_response

from tests.simulator.unit.calculations.test_profit import NOW


def test_half_even_and_half_up_rounding_are_explicit() -> None:
    """The same tie follows the selected provider rounding rule exactly."""
    common = {
        "amount": Decimal("1.005"),
        "source_currency": "USD",
        "target_currency": "USD",
        "as_of": NOW,
        "currency_digits": 2,
        "evidence": None,
    }
    even = unwrap_simulation_response(
        convert_account_currency(**common, rounding_rule="ROUND_HALF_EVEN"),
        operation="test.round_even",
    )
    up = unwrap_simulation_response(
        convert_account_currency(**common, rounding_rule="ROUND_HALF_UP"),
        operation="test.round_up",
    )
    assert even == Decimal("1.00")
    assert up == Decimal("1.01")
