"""Unit tests for exact unit primitives."""

from decimal import Decimal

import pytest
from app.utils import add_exact, build_exact_unit, compare_exact, quantize_exact
from app.utils.errors.exceptions import ValidationError


def test_float_input_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_exact_unit(1.2, kind="MONEY", currency="USD")  # type: ignore[arg-type]


def test_money_plus_quantity_is_rejected() -> None:
    money = build_exact_unit("1", kind="MONEY", currency="USD")
    quantity = build_exact_unit("1", kind="QUANTITY")
    with pytest.raises(ValidationError):
        add_exact(money, quantity)


def test_arithmetic_and_quantization_are_exact() -> None:
    left = build_exact_unit(Decimal("1.25"), kind="MONEY", currency="USD")
    right = build_exact_unit("2.25", kind="MONEY", currency="USD")
    assert add_exact(left, right)["amount"] == "3.50"
    assert compare_exact(left, right) == -1
    assert quantize_exact(right, "0.1", direction="DOWN")["amount"] == "2.2"
