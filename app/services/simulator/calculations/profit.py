"""Exact evidenced MT5-FX profit calculation."""

from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.simulator.calculations.fx import convert

if TYPE_CHECKING:
    from app.services.simulator.calculations.contracts import CalculationSpecification


def calculate(
    specification: CalculationSpecification,
    *,
    side: str,
    volume: Decimal,
    open_price: Decimal,
    close_price: Decimal,
    as_of: object,
    fx_evidence: object | None,
) -> Decimal:
    """Calculate signed FX profit and convert to account currency.

    Args:
        specification: Effective calculation specification.
        side: ``BUY`` or ``SELL``.
        volume: Positive lot volume.
        open_price: Positive opening price.
        close_price: Positive closing price.
        as_of: Aware-UTC calculation instant.
        fx_evidence: Optional Data-owned currency conversion evidence.

    Returns:
        Rounded account-currency profit.

    Raises:
        ValueError: If inputs, mode, revision, or conversion are invalid.
    """
    from datetime import datetime

    if side not in {"BUY", "SELL"}:
        raise ValueError("side must be BUY or SELL")
    if not isinstance(as_of, datetime) or not specification.covers(as_of):
        raise ValueError("specification does not cover calculation instant")
    if any(
        not value.is_finite() or value <= 0
        for value in (volume, open_price, close_price)
    ):
        raise ValueError("profit inputs must be finite and positive")
    direction = Decimal(1) if side == "BUY" else Decimal(-1)
    profit = (
        direction * (close_price - open_price) * specification.contract_size * volume
    )
    return convert(
        profit,
        source_currency=specification.profit_currency,
        target_currency=specification.account_currency,
        as_of=as_of,
        currency_digits=specification.currency_digits,
        rounding_rule=specification.rounding_rule,
        evidence=fx_evidence,
    )


__all__ = ["calculate"]
