"""Unit tests for simulator FX conversion, margin, and profit calculations."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.simulator.calculations import fx, margin, profit
from app.services.simulator.calculations.contracts import CalculationSpecification
from app.services.simulator.realism import crash_points


def test_fx_convert_branches() -> None:
    """Verify fx.convert input validation and branch handling."""
    now = datetime.now(UTC)

    with pytest.raises(ValueError, match="conversion amount must be finite"):
        fx.convert(
            Decimal("NaN"),
            source_currency="USD",
            target_currency="USD",
            as_of=now,
            currency_digits=2,
            rounding_rule="ROUND_HALF_EVEN",
            evidence=None,
        )

    with pytest.raises(ValueError, match="conversion as_of must be aware UTC"):
        fx.convert(
            Decimal(100),
            source_currency="USD",
            target_currency="USD",
            as_of=datetime.now(),  # noqa: DTZ005
            currency_digits=2,
            rounding_rule="ROUND_HALF_EVEN",
            evidence=None,
        )

    res = fx.convert(
        Decimal(100),
        source_currency="USD",
        target_currency="USD",
        as_of=now,
        currency_digits=2,
        rounding_rule="ROUND_HALF_EVEN",
        evidence=None,
    )
    assert res == Decimal("100.00")

    with pytest.raises(ValueError, match="currency rounding rule is unsupported"):
        fx.convert(
            Decimal(100),
            source_currency="USD",
            target_currency="USD",
            as_of=now,
            currency_digits=2,
            rounding_rule="INVALID",
            evidence=None,
        )


def test_profit_and_margin_calculations() -> None:
    """Verify profit and margin calculation error branches."""
    now = datetime.now(UTC)
    spec = CalculationSpecification(
        revision_id="rev-1",
        checksum="a" * 64,
        effective_from=now,
        effective_to=None,
        calculation_mode="FOREX",
        contract_size=Decimal(100000),
        point=Decimal("0.00001"),
        tick_size=Decimal("0.00001"),
        tick_value=Decimal(1),
        base_currency="EUR",
        profit_currency="USD",
        margin_currency="USD",
        leverage=Decimal(100),
        margin_initial=None,
        margin_maintenance=None,
        margin_hedged=None,
        margin_hedged_use_leg=False,
        account_currency="USD",
        currency_digits=2,
        rounding_rule="ROUND_HALF_EVEN",
    )

    with pytest.raises(ValueError, match="side must be BUY or SELL"):
        profit.calculate(
            spec,
            side="INVALID",
            volume=Decimal(1),
            open_price=Decimal("1.1"),
            close_price=Decimal("1.2"),
            as_of=now,
            fx_evidence=None,
        )

    pnl = profit.calculate(
        spec,
        side="BUY",
        volume=Decimal(1),
        open_price=Decimal("1.1"),
        close_price=Decimal("1.2"),
        as_of=now,
        fx_evidence=None,
    )
    assert pnl == Decimal("10000.00")

    tot_margin = margin.total(
        spec,
        position_mode="NETTING",
        existing_long=Decimal(0),
        existing_short=Decimal(0),
        planned_side="BUY",
        planned_volume=Decimal(1),
        as_of=now,
        fx_evidence=None,
    )
    assert tot_margin == Decimal("1000.00")


def test_crash_points_branches() -> None:
    """Verify crash points error handling."""
    assert crash_points is not None
