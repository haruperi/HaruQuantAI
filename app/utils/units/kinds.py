"""Closed unit-kind taxonomy."""

from app.utils.errors.exceptions import ValidationError

_KINDS = (
    "MONEY",
    "PRICE",
    "QUANTITY",
    "PERCENTAGE",
    "BASIS_POINTS",
    "TICKS",
    "POINTS",
    "LOTS",
    "CONTRACTS",
    "SHARES",
)


def get_supported_unit_kinds() -> tuple[str, ...]:
    """Return the closed supported unit-kind set.

    Returns:
        Supported uppercase unit kinds.
    """
    return _KINDS


def unit_kind_requires_currency(kind: str) -> bool:
    """Return whether a supported kind requires ISO currency evidence.

    Args:
        kind: Supported unit kind.

    Returns:
        Whether currency is required.

    Raises:
        ValidationError: If the kind is unsupported.
    """
    if kind not in _KINDS:
        raise ValidationError("UNIT_KIND_INVALID")
    return kind == "MONEY"
