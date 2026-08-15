"""Unit tests for effective MT5 provider semantics."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.simulator.execution.provider_semantics import validate_provider_order

NOW = datetime(2026, 8, 16, 10, tzinfo=UTC)


def _revision(**updates: object) -> dict[str, object]:
    payload = {
        "trade_mode": "FULL",
        "filling_modes": ("FOK", "IOC"),
        "execution_mode": "MARKET",
        "directional_volume_limit": "2",
        "point": "0.00001",
        "stops_level_points": 10,
        "freeze_level_points": 5,
    }
    payload.update(updates)
    return {
        "complete_coverage": True,
        "effective_from": NOW - timedelta(days=1),
        "effective_to": NOW + timedelta(days=1),
        "payload": payload,
    }


def test_stops_freeze_modes_and_directional_limit_are_exact() -> None:
    """Order admission uses positions plus pending volume and exact boundaries."""
    with pytest.raises(ValueError, match="directional"):
        validate_provider_order(
            _revision(),
            at=NOW,
            action="OPEN",
            fill_policy="FOK",
            execution_mode="MARKET",
            requested_volume=Decimal(1),
            same_direction_position_volume=Decimal(1),
            same_direction_pending_volume=Decimal("0.01"),
            reference_price=Decimal("1.1"),
        )
    with pytest.raises(ValueError, match="stop level"):
        validate_provider_order(
            _revision(),
            at=NOW,
            action="OPEN",
            fill_policy="FOK",
            execution_mode="MARKET",
            requested_volume=Decimal("0.1"),
            same_direction_position_volume=Decimal(0),
            same_direction_pending_volume=Decimal(0),
            reference_price=Decimal("1.10000"),
            stop_price=Decimal("1.09995"),
        )


def test_disabled_close_only_and_unsupported_modes_fail_closed() -> None:
    """Trade, fill, and execution modes come only from the effective revision."""
    for revision, expected in (
        (_revision(trade_mode="DISABLED"), "trade mode"),
        (_revision(trade_mode="CLOSE_ONLY"), "close-only"),
        (_revision(filling_modes=("IOC",)), "filling"),
        (_revision(execution_mode="INSTANT"), "execution"),
    ):
        with pytest.raises(ValueError, match=expected):
            validate_provider_order(
                revision,
                at=NOW,
                action="OPEN",
                fill_policy="FOK",
                execution_mode="MARKET",
                requested_volume=Decimal("0.1"),
                same_direction_position_volume=Decimal(0),
                same_direction_pending_volume=Decimal(0),
                reference_price=Decimal("1.1"),
            )
