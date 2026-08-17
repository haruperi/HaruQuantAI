"""Unit tests for simulator rollover scheduling and swap accounting."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.simulator.accounting.swap import (
    calculate_swap_rollover,
    schedule_rollover,
)


def test_schedule_rollover_and_swap_branches() -> None:
    """Verify schedule_rollover and calculate_swap_rollover error handling and options."""
    now = datetime.now(UTC)

    # Naive timezone check
    with pytest.raises(ValueError, match="rollover scheduling requires aware UTC"):
        schedule_rollover(datetime.now(), "UTC")  # noqa: DTZ005

    # Invalid timezone
    with pytest.raises(ValueError, match="server timezone is unavailable"):
        schedule_rollover(now, "Invalid/TZ")

    # Invalid clock
    with pytest.raises(ValueError, match="server rollover clock is invalid"):
        schedule_rollover(now, "UTC", hour=25)

    # Valid rollover scheduling
    roll = schedule_rollover(now, "UTC", hour=0, minute=0)
    assert roll.tzinfo == UTC

    # Calculate swap error branches
    with pytest.raises(ValueError, match="rollover timestamp must be aware UTC"):
        calculate_swap_rollover(
            rollover_at=datetime.now(),  # noqa: DTZ005
            server_timezone="UTC",
            side="LONG",
            volume=Decimal(1),
            rate=Decimal("0.5"),
            weekday_ratios={i: Decimal(1) for i in range(7)},
            unit="ACCOUNT_CURRENCY",
            point_value=None,
            fx_rate=None,
            posting_mode="ACCRUAL_ONLY",
            position_id="pos-1",
        )

    with pytest.raises(ValueError, match="swap position input is invalid"):
        calculate_swap_rollover(
            rollover_at=now,
            server_timezone="UTC",
            side="INVALID",
            volume=Decimal(1),
            rate=Decimal("0.5"),
            weekday_ratios={i: Decimal(1) for i in range(7)},
            unit="ACCOUNT_CURRENCY",
            point_value=None,
            fx_rate=None,
            posting_mode="ACCRUAL_ONLY",
            position_id="pos-1",
        )
