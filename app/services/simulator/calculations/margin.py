"""Exact evidenced MT5-FX netting and hedging margin."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, cast

from app.services.simulator.calculations.fx import convert

if TYPE_CHECKING:
    from app.services.simulator.calculations.contracts import CalculationSpecification


def _base(specification: CalculationSpecification, volume: Decimal) -> Decimal:
    """Return unconverted FOREX margin for an absolute volume.

    Args:
        specification: Effective calculation specification.
        volume: Non-negative lot volume.

    Returns:
        Exact margin-currency amount.
    """
    if specification.margin_initial is not None and specification.margin_initial > 0:
        return volume * specification.margin_initial
    return volume * specification.contract_size / specification.leverage


def total(
    specification: CalculationSpecification,
    *,
    position_mode: str,
    existing_long: Decimal,
    existing_short: Decimal,
    planned_side: str,
    planned_volume: Decimal,
    as_of: datetime,
    fx_evidence: object | None,
) -> Decimal:
    """Calculate total margin after one planned FX order.

    Args:
        specification: Effective calculation specification.
        position_mode: ``NETTING`` or ``HEDGING``.
        existing_long: Existing long lots.
        existing_short: Existing short lots.
        planned_side: ``BUY`` or ``SELL``.
        planned_volume: Planned positive lots.
        as_of: Aware-UTC calculation instant.
        fx_evidence: Optional Data-owned conversion evidence.

    Returns:
        Rounded total account-currency margin.

    Raises:
        ValueError: If mode, exposure, revision, or conversion is invalid.
    """
    if not specification.covers(as_of):
        raise ValueError("specification does not cover calculation instant")
    if position_mode not in {"NETTING", "HEDGING"} or planned_side not in {
        "BUY",
        "SELL",
    }:
        raise ValueError("position mode or side is unsupported")
    if any(
        not value.is_finite() or value < 0 for value in (existing_long, existing_short)
    ):
        raise ValueError("existing exposure must be finite and non-negative")
    if not planned_volume.is_finite() or planned_volume < 0:
        raise ValueError("planned volume must be finite and non-negative")
    long_volume = existing_long + (planned_volume if planned_side == "BUY" else 0)
    short_volume = existing_short + (planned_volume if planned_side == "SELL" else 0)
    if position_mode == "NETTING":
        raw = _base(specification, abs(long_volume - short_volume))
    elif specification.margin_hedged_use_leg:
        raw = max(_base(specification, long_volume), _base(specification, short_volume))
    else:
        hedged = min(long_volume, short_volume)
        uncovered = abs(long_volume - short_volume)
        hedged_rate = specification.margin_hedged or Decimal(0)
        raw = _base(specification, uncovered) + hedged * hedged_rate
    return convert(
        raw,
        source_currency=specification.margin_currency,
        target_currency=specification.account_currency,
        as_of=as_of,
        currency_digits=specification.currency_digits,
        rounding_rule=specification.rounding_rule,
        evidence=fx_evidence,
    )


def planned(specification: CalculationSpecification, **fields: object) -> Decimal:
    """Return incremental non-negative margin for one planned order.

    Args:
        specification: Effective calculation specification.
        **fields: Arguments accepted by :func:`total`.

    Returns:
        Incremental rounded account-currency margin.

    Raises:
        TypeError: If planned volume is not an exact Decimal.
    """
    planned_volume = fields["planned_volume"]
    if not isinstance(planned_volume, Decimal):
        raise TypeError("planned_volume must be Decimal")
    common = {
        "position_mode": cast("str", fields["position_mode"]),
        "existing_long": cast("Decimal", fields["existing_long"]),
        "existing_short": cast("Decimal", fields["existing_short"]),
        "planned_side": cast("str", fields["planned_side"]),
        "as_of": cast("datetime", fields["as_of"]),
        "fx_evidence": fields.get("fx_evidence"),
    }
    after = total(specification, planned_volume=planned_volume, **common)  # type: ignore[arg-type]
    before = total(specification, planned_volume=Decimal(0), **common)  # type: ignore[arg-type]
    quantum = Decimal(1).scaleb(-specification.currency_digits)
    before = before.quantize(quantum)
    return max(after - before, Decimal(0)).quantize(quantum)


__all__ = ["planned", "total"]
