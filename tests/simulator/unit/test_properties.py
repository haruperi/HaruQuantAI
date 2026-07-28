"""Table-driven property checks for Simulation numeric invariants."""

from decimal import Decimal

import pytest
from app.services.simulator import (
    SimulationError,
    SymbolSpecification,
    calculate_margin,
    normalize_volume,
)
from app.services.simulator.errors import unwrap_simulation_response


def _value(response: object) -> object:
    """Return the raw payload from a public Simulation response."""
    return unwrap_simulation_response(response, operation="test.properties")


def _specification() -> SymbolSpecification:
    """Build bounded FX symbol evidence for numeric property checks."""
    return SymbolSpecification(
        minimum_volume=Decimal("0.01"),
        maximum_volume=Decimal(100),
        volume_step=Decimal("0.01"),
        contract_size=Decimal(100000),
        leverage=Decimal(100),
    )


@pytest.mark.parametrize(
    "volume",
    [Decimal("0.01"), Decimal("0.10"), Decimal("1.00"), Decimal("99.99")],
)
def test_normalize_volume_preserves_every_aligned_approved_value(
    volume: Decimal,
) -> None:
    """Preserve every bounded step-aligned Risk-approved volume exactly."""
    assert _value(normalize_volume(volume, _specification())) == volume


@pytest.mark.parametrize(
    ("volume", "expected_code"),
    [
        (Decimal(-1), "SIM_INVALID_VOLUME"),
        (Decimal(0), "SIM_INVALID_VOLUME"),
        (Decimal("0.001"), "SIM_VOLUME_BELOW_MIN"),
        (Decimal("0.015"), "SIM_VOLUME_STEP_MISMATCH"),
        (Decimal("100.01"), "SIM_VOLUME_ABOVE_MAX"),
        (Decimal("NaN"), "SIM_INVALID_VOLUME"),
        (Decimal("Infinity"), "SIM_INVALID_VOLUME"),
    ],
)
def test_normalize_volume_rejects_every_invalid_numeric_class(
    volume: Decimal,
    expected_code: str,
) -> None:
    """Fail closed for non-positive, unaligned, out-of-bound, or unsafe values."""
    with pytest.raises(SimulationError) as captured:
        _value(normalize_volume(volume, _specification()))
    assert captured.value.code == expected_code


@pytest.mark.parametrize(
    ("volume", "price", "contract_size", "leverage", "expected"),
    [
        ("1", "1.1", "100000", "100", "1100"),
        ("0.01", "2000", "100", "20", "100"),
        ("2.5", "10", "1000", "50", "500"),
    ],
)
def test_margin_formula_is_exact_and_deterministic(
    volume: str,
    price: str,
    contract_size: str,
    leverage: str,
    expected: str,
) -> None:
    """Apply the documented Decimal margin formula without float drift."""
    inputs = tuple(Decimal(value) for value in (volume, price, contract_size, leverage))
    assert _value(calculate_margin(inputs[0], inputs[1], inputs[2], inputs[3])) == Decimal(
        expected
    )
