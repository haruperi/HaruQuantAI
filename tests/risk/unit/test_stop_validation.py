"""Unit tests for stop-loss validation contracts and checks."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.risk.contracts import LimitStatus
from app.services.risk.contracts.responses import unwrap_risk_response
from app.services.risk.stop_validation import (
    build_stop_validation,
    parse_stop_validation,
    validate_stop_loss,
)
from pydantic import ValidationError

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _validation(**overrides: object) -> dict[str, object]:
    """Build a bounded valid BUY stop-validation mapping."""
    values: dict[str, object] = {
        "symbol": "EURUSD",
        "side": "BUY",
        "entry_price": Decimal("1.1000"),
        "stop_price": Decimal("1.0950"),
        "tick_size": Decimal("0.0001"),
        "min_stop_distance": Decimal("0.0020"),
        "contract_value": Decimal(100000),
        "quantity": Decimal("0.1"),
        "evaluated_at": NOW,
    }
    values.update(overrides)
    return build_stop_validation(**values)


def test_build_and_parse_round_trip() -> None:
    """Round-trip a StopValidation v1 mapping through build/parse."""
    built = _validation()
    parsed = parse_stop_validation(built)
    assert parsed["schema_id"] == "risk.stop_validation.v1"
    assert parsed["symbol"] == "EURUSD"


def test_parse_rejects_invalid_mapping() -> None:
    """Reject a mapping with a non-finite stop price."""
    with pytest.raises(ValidationError):
        parse_stop_validation({**_validation(), "stop_price": None})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("symbol", "   "),
        ("entry_price", Decimal(0)),
        ("stop_price", Decimal(-1)),
        ("tick_size", Decimal(0)),
        ("min_stop_distance", Decimal(-1)),
        ("contract_value", Decimal(0)),
        ("quantity", Decimal(0)),
        ("invalidation_price", Decimal(0)),
        ("previous_stop_price", Decimal(0)),
    ],
)
def test_parse_rejects_invalid_field_values(field: str, value: object) -> None:
    """Reject every invalid StopValidation v1 field value."""
    with pytest.raises(ValidationError):
        parse_stop_validation({**_validation(), field: value})


def test_valid_stop_passes_every_check() -> None:
    """Pass side, tick, distance, and widening checks for a valid stop."""
    results = unwrap_risk_response(
        validate_stop_loss(_validation()), operation="validate_stop_loss"
    )
    by_id = {item.limit_id: item for item in results}
    assert by_id["stop_side"].status is LimitStatus.PASS
    assert by_id["stop_tick"].status is LimitStatus.PASS
    assert by_id["stop_noise_distance"].status is LimitStatus.PASS
    assert by_id["stop_projected_loss"].observed_value == Decimal("50.00000")


def test_wrong_side_stop_fails() -> None:
    """Fail the side check when a BUY stop is above entry."""
    results = unwrap_risk_response(
        validate_stop_loss(_validation(stop_price=Decimal("1.1050"))),
        operation="validate_stop_loss",
    )
    by_id = {item.limit_id: item for item in results}
    assert by_id["stop_side"].status is LimitStatus.FAIL


def test_noise_distance_fails_when_too_close() -> None:
    """Fail the noise-distance check when the stop is inside the venue floor."""
    results = unwrap_risk_response(
        validate_stop_loss(_validation(stop_price=Decimal("1.0995"))),
        operation="validate_stop_loss",
    )
    by_id = {item.limit_id: item for item in results}
    assert by_id["stop_noise_distance"].status is LimitStatus.FAIL


def test_widening_blocked_without_permission() -> None:
    """Block a looser BUY stop than the previous one without widening permission."""
    results = unwrap_risk_response(
        validate_stop_loss(
            _validation(previous_stop_price=Decimal("1.0960"), allow_widening=False)
        ),
        operation="validate_stop_loss",
    )
    by_id = {item.limit_id: item for item in results}
    assert by_id["stop_widening_permission"].status is LimitStatus.FAIL


def test_widening_allowed_with_explicit_permission() -> None:
    """Allow a looser stop when widening permission is explicitly granted."""
    results = unwrap_risk_response(
        validate_stop_loss(
            _validation(previous_stop_price=Decimal("1.0960"), allow_widening=True)
        ),
        operation="validate_stop_loss",
    )
    by_id = {item.limit_id: item for item in results}
    assert by_id["stop_widening_permission"].status is LimitStatus.PASS


def test_invalidation_distance_fails_when_stop_short_of_invalidation() -> None:
    """Fail when the stop is placed before the structural invalidation level."""
    results = unwrap_risk_response(
        validate_stop_loss(_validation(invalidation_price=Decimal("1.0900"))),
        operation="validate_stop_loss",
    )
    by_id = {item.limit_id: item for item in results}
    assert by_id["stop_invalidation_distance"].status is LimitStatus.FAIL
