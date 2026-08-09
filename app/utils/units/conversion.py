"""Explicit-direction exact-unit quantization."""

from collections.abc import Mapping
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP, Decimal

from app.utils.errors.exceptions import ValidationError
from app.utils.units.amounts import build_exact_unit, parse_exact_unit

_ROUNDING = {"DOWN": ROUND_DOWN, "UP": ROUND_UP, "HALF_EVEN": ROUND_HALF_EVEN}


def get_max_decimal_places() -> int:
    """Return the shared supported decimal-place ceiling.

    Returns:
        Maximum decimal places.
    """
    return 28


def quantize_exact(
    value: Mapping[str, object], increment: Decimal | int | str, *, direction: str
) -> dict[str, str | None]:
    """Quantize an exact unit to a positive increment.

    Args:
        value: ExactUnit v1 mapping.
        increment: Positive exact increment.
        direction: Explicit rounding direction.

    Returns:
        Quantized ExactUnit v1 mapping.

    Raises:
        ValidationError: If an argument is invalid.
    """
    parsed = parse_exact_unit(value)
    if direction not in _ROUNDING:
        raise ValidationError("ROUNDING_DIRECTION_INVALID")
    if isinstance(increment, bool | float):
        raise ValidationError("QUANTIZATION_INCREMENT_INVALID")
    step = Decimal(increment)
    exponent = step.as_tuple().exponent
    decimal_places = -exponent if isinstance(exponent, int) and exponent < 0 else 0
    if not step.is_finite() or step <= 0 or decimal_places > get_max_decimal_places():
        raise ValidationError("QUANTIZATION_INCREMENT_INVALID")
    amount = Decimal(str(parsed["amount"]))
    quantized = (amount / step).to_integral_value(rounding=_ROUNDING[direction]) * step
    return build_exact_unit(
        quantized, kind=str(parsed["kind"]), currency=parsed["currency"]
    )
