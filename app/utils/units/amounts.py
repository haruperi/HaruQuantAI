"""Immutable exact financial-unit mappings and checked arithmetic."""

from __future__ import annotations

import re
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation

from app.utils.errors.exceptions import ValidationError
from app.utils.units.kinds import get_supported_unit_kinds, unit_kind_requires_currency

_CURRENCY = re.compile(r"[A-Z]{3}\Z")
_FIELDS = {"contract_version", "schema_id", "amount", "kind", "currency"}


def _decimal(value: object) -> Decimal:
    """Validate and convert an exact scalar.

    Args:
        value: Exact candidate value.

    Returns:
        Finite Decimal value.

    Raises:
        ValidationError: If the value is inexact or non-finite.
    """
    if isinstance(value, bool | float) or not isinstance(value, Decimal | int | str):
        raise ValidationError("EXACT_VALUE_INVALID")
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValidationError("EXACT_VALUE_INVALID") from error
    if not result.is_finite():
        raise ValidationError("EXACT_VALUE_INVALID")
    return result


def build_exact_unit(
    amount: Decimal | int | str, *, kind: str, currency: str | None = None
) -> dict[str, str | None]:
    """Build an ExactUnit v1 mapping without accepting binary floats.

    Args:
        amount: Exact amount.
        kind: Supported unit kind.
        currency: ISO currency for money.

    Returns:
        ExactUnit v1 mapping.

    Raises:
        ValidationError: If unit evidence is invalid.
    """
    if kind not in get_supported_unit_kinds():
        raise ValidationError("UNIT_KIND_INVALID")
    needs_currency = unit_kind_requires_currency(kind)
    if needs_currency != (currency is not None):
        raise ValidationError("UNIT_CURRENCY_INVALID")
    if currency is not None and _CURRENCY.fullmatch(currency) is None:
        raise ValidationError("UNIT_CURRENCY_INVALID")
    return {
        "contract_version": "v1",
        "schema_id": "utils.exact_unit.v1",
        "amount": format(_decimal(amount), "f"),
        "kind": kind,
        "currency": currency,
    }


def parse_exact_unit(value: Mapping[str, object]) -> dict[str, str | None]:
    """Validate and detach an ExactUnit v1 mapping.

    Args:
        value: Candidate mapping.

    Returns:
        Detached ExactUnit v1 mapping.

    Raises:
        ValidationError: If validation fails.
    """
    if (
        set(value) != _FIELDS
        or value.get("contract_version") != "v1"
        or value.get("schema_id") != "utils.exact_unit.v1"
    ):
        raise ValidationError("EXACT_UNIT_INVALID")
    amount = value.get("amount")
    kind = value.get("kind")
    currency = value.get("currency")
    if (
        not isinstance(amount, str)
        or not isinstance(kind, str)
        or (currency is not None and not isinstance(currency, str))
    ):
        raise ValidationError("EXACT_UNIT_INVALID")
    return build_exact_unit(amount, kind=kind, currency=currency)


def _compatible(
    left: Mapping[str, object], right: Mapping[str, object]
) -> tuple[dict[str, str | None], dict[str, str | None]]:
    """Validate compatible operands.

    Args:
        left: Left ExactUnit mapping.
        right: Right ExactUnit mapping.

    Returns:
        Parsed compatible operands.

    Raises:
        ValidationError: If units differ.
    """
    parsed_left, parsed_right = parse_exact_unit(left), parse_exact_unit(right)
    if (parsed_left["kind"], parsed_left["currency"]) != (
        parsed_right["kind"],
        parsed_right["currency"],
    ):
        raise ValidationError("UNIT_MISMATCH")
    return parsed_left, parsed_right


def add_exact(
    left: Mapping[str, object], right: Mapping[str, object]
) -> dict[str, str | None]:
    """Add compatible exact units.

    Args:
        left: Left operand.
        right: Right operand.

    Returns:
        Exact sum.
    """
    left_value, right_value = _compatible(left, right)
    return build_exact_unit(
        _decimal(left_value["amount"]) + _decimal(right_value["amount"]),
        kind=str(left_value["kind"]),
        currency=left_value["currency"],
    )


def subtract_exact(
    left: Mapping[str, object], right: Mapping[str, object]
) -> dict[str, str | None]:
    """Subtract compatible exact units.

    Args:
        left: Left operand.
        right: Right operand.

    Returns:
        Exact difference.
    """
    left_value, right_value = _compatible(left, right)
    return build_exact_unit(
        _decimal(left_value["amount"]) - _decimal(right_value["amount"]),
        kind=str(left_value["kind"]),
        currency=left_value["currency"],
    )


def scale_exact(
    value: Mapping[str, object], scalar: Decimal | int | str
) -> dict[str, str | None]:
    """Scale an exact unit by an exact scalar.

    Args:
        value: ExactUnit mapping.
        scalar: Exact scalar.

    Returns:
        Scaled exact unit.
    """
    parsed = parse_exact_unit(value)
    return build_exact_unit(
        _decimal(parsed["amount"]) * _decimal(scalar),
        kind=str(parsed["kind"]),
        currency=parsed["currency"],
    )


def compare_exact(left: Mapping[str, object], right: Mapping[str, object]) -> int:
    """Return ordering for compatible exact units.

    Args:
        left: Left operand.
        right: Right operand.

    Returns:
        Negative, zero, or positive comparison value.
    """
    left_value, right_value = _compatible(left, right)
    return (_decimal(left_value["amount"]) > _decimal(right_value["amount"])) - (
        _decimal(left_value["amount"]) < _decimal(right_value["amount"])
    )
