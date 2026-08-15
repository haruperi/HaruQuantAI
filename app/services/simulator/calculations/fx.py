"""Evidence-bound exact account-currency conversion."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal
from typing import Any

from app.services.data import is_fx_conversion_evidence

_ROUNDING = {"ROUND_HALF_EVEN": ROUND_HALF_EVEN, "ROUND_HALF_UP": ROUND_HALF_UP}
_MAX_CURRENCY_DIGITS = 12


def convert(
    amount: Decimal,
    *,
    source_currency: str,
    target_currency: str,
    as_of: datetime,
    currency_digits: int,
    rounding_rule: str,
    evidence: object | None,
) -> Decimal:
    """Convert and round using only supplied Data-owned evidence.

    Args:
        amount: Exact source-currency amount.
        source_currency: Source ISO currency.
        target_currency: Target ISO currency.
        as_of: Aware-UTC calculation instant.
        currency_digits: Provider-documented target digits.
        rounding_rule: Provider-documented Decimal rounding rule.
        evidence: Data-owned FX conversion evidence, unless currencies match.

    Returns:
        Exact rounded target-currency amount.

    Raises:
        ValueError: If evidence, time, path, amount, or rounding is invalid.
    """
    if not amount.is_finite():
        raise ValueError("conversion amount must be finite")
    if as_of.tzinfo is None or as_of.utcoffset() != UTC.utcoffset(as_of):
        raise ValueError("conversion as_of must be aware UTC")
    rate = Decimal(1)
    if source_currency != target_currency:
        if evidence is None or not is_fx_conversion_evidence(evidence):
            raise ValueError("FX conversion evidence is required")
        item: Any = evidence
        if (
            item.source_currency != source_currency
            or item.target_currency != target_currency
        ):
            raise ValueError("FX conversion evidence currency mismatch")
        if not item.as_of <= as_of < item.expires_at:
            raise ValueError("FX conversion evidence is not valid at as_of")
        if len(item.legs) not in {1, 2}:
            raise ValueError("only evidenced direct/inverse/two-leg paths are admitted")
        rate = Decimal(item.composite_rate)
    if (
        rounding_rule not in _ROUNDING
        or not 0 <= currency_digits <= _MAX_CURRENCY_DIGITS
    ):
        raise ValueError("currency rounding rule is unsupported")
    quantum = Decimal(1).scaleb(-currency_digits)
    return (amount * rate).quantize(quantum, rounding=_ROUNDING[rounding_rule])


__all__ = ["convert"]
