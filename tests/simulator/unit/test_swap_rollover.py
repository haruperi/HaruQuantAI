"""Unit evidence for broker-server rollover swap semantics."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.simulator import calculate_rollover_swap, schedule_simulation_rollover

RATIOS = {day: Decimal(3 if day == 2 else 1) for day in range(7)}


@pytest.mark.parametrize("weekday", range(7))
def test_fr_sim_134_135_205_every_weekday_ratio(weekday: int) -> None:
    """FR-SIM-134/135/205: server weekday selects the exact ratio."""
    rollover = datetime(2026, 8, 10 + weekday, tzinfo=UTC)
    result = calculate_rollover_swap(
        rollover_at=rollover,
        server_timezone="UTC",
        side="LONG",
        volume=Decimal(2),
        rate=Decimal("-0.5"),
        weekday_ratios=RATIOS,
        unit="ACCOUNT_CURRENCY",
        point_value=None,
        fx_rate=None,
        posting_mode="ACCRUAL_ONLY",
        position_id="position-1",
    )
    assert result["weekday"] == weekday
    assert Decimal(str(result["accrued_amount"])) == Decimal(-1) * RATIOS[weekday]


def test_fr_sim_206_units_fx_and_missingness() -> None:
    """FR-SIM-206: exact units convert only through explicit evidence."""
    common = {
        "rollover_at": datetime(2026, 8, 12, tzinfo=UTC),
        "server_timezone": "UTC",
        "side": "SHORT",
        "volume": Decimal(1),
        "rate": Decimal(2),
        "weekday_ratios": RATIOS,
        "posting_mode": "ACCRUAL_ONLY",
        "position_id": "position-1",
    }
    points = calculate_rollover_swap(
        **common, unit="POINTS", point_value=Decimal("0.1"), fx_rate=None
    )
    assert points["accrued_amount"] == "0.6"
    with pytest.raises(ValueError, match="FX evidence"):
        calculate_rollover_swap(
            **common,
            unit="PROFIT_CURRENCY",
            point_value=None,
            fx_rate=None,
        )


def test_fr_sim_207_208_posting_and_reopen_require_evidence() -> None:
    """FR-SIM-207/208: posting and REOPEN remain evidence-gated."""
    fields = {
        "rollover_at": datetime(2026, 8, 12, tzinfo=UTC),
        "server_timezone": "UTC",
        "side": "LONG",
        "volume": Decimal(1),
        "rate": Decimal(-1),
        "weekday_ratios": RATIOS,
        "unit": "ACCOUNT_CURRENCY",
        "point_value": None,
        "fx_rate": None,
        "position_id": "position-1",
    }
    with pytest.raises(ValueError, match="target evidence"):
        calculate_rollover_swap(**fields, posting_mode="BALANCE_POSTING")
    posted = calculate_rollover_swap(
        **fields,
        posting_mode="BALANCE_POSTING",
        posting_evidence_reference="provider-deal-fixture",
    )
    assert posted["balance_posted"] is True
    reopened = calculate_rollover_swap(
        **fields,
        posting_mode="REOPEN",
        posting_evidence_reference="provider-deal-fixture",
    )
    assert reopened["reopened_position_id"] != "position-1"


def test_rollover_schedule_respects_dst_offset_changes() -> None:
    """Next server rollover follows timezone rules across DST transitions."""
    summer = schedule_simulation_rollover(
        datetime(2026, 6, 1, tzinfo=UTC), "Europe/London", hour=2
    )
    winter = schedule_simulation_rollover(
        datetime(2026, 12, 1, tzinfo=UTC), "Europe/London", hour=2
    )
    assert summer.hour == 1
    assert winter.hour == 2
