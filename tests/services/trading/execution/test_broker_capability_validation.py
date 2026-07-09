"""Unit tests for broker adapter capability validation primitives."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.execution.broker_capability_validation import (
    BrokerCapabilityProfile,
    requires_cancel_on_disconnect_failsafe,
    validate_broker_capabilities,
    validate_filling_mode_capability,
    validate_order_type_capability,
    validate_precision_capability,
    validate_rate_limit_capability,
)
from app.services.trading.security.error_mapping import TradingValidationError


def _profile(**overrides: object) -> BrokerCapabilityProfile:
    defaults: dict[str, object] = {
        "provider": "mt5",
        "supported_order_types": ("market", "limit", "stop"),
        "supported_filling_modes": ("IOC", "FOK"),
        "price_precision_digits": 5,
        "volume_precision_step": Decimal("0.01"),
        "max_requests_per_second": Decimal(10),
        "supports_cancel_on_disconnect": False,
    }
    defaults.update(overrides)
    return BrokerCapabilityProfile(**defaults)  # type: ignore[arg-type]


def test_broker_capability_profile_rejects_blank_provider() -> None:
    """BrokerCapabilityProfile fails closed on a blank provider."""
    with pytest.raises(ValueError, match="provider"):
        _profile(provider=" ")


def test_broker_capability_profile_rejects_empty_order_types() -> None:
    """BrokerCapabilityProfile fails closed on an empty order type set."""
    with pytest.raises(ValueError, match="supported_order_types"):
        _profile(supported_order_types=())


def test_broker_capability_profile_rejects_empty_filling_modes() -> None:
    """BrokerCapabilityProfile fails closed on an empty filling mode set."""
    with pytest.raises(ValueError, match="supported_filling_modes"):
        _profile(supported_filling_modes=())


def test_validate_order_type_capability() -> None:
    """Order type validation passes for supported types and fails otherwise."""
    profile = _profile()
    validate_order_type_capability(profile=profile, order_type="market")
    with pytest.raises(TradingValidationError):
        validate_order_type_capability(profile=profile, order_type="stop_limit")


def test_validate_filling_mode_capability() -> None:
    """Filling mode validation passes for supported modes and fails otherwise."""
    profile = _profile()
    validate_filling_mode_capability(profile=profile, filling_mode="IOC")
    with pytest.raises(TradingValidationError):
        validate_filling_mode_capability(profile=profile, filling_mode="RETURN")


def test_validate_precision_capability_rejects_excess_price_precision() -> None:
    """Precision validation fails closed on excess price decimal digits."""
    profile = _profile(price_precision_digits=2)
    with pytest.raises(TradingValidationError):
        validate_precision_capability(
            profile=profile, price=Decimal("1.12345"), volume=Decimal("0.01")
        )


def test_validate_precision_capability_rejects_misaligned_volume() -> None:
    """Precision validation fails closed on a volume step misalignment."""
    profile = _profile()
    with pytest.raises(TradingValidationError):
        validate_precision_capability(
            profile=profile, price=Decimal("1.10"), volume=Decimal("0.015")
        )


def test_validate_precision_capability_passes_for_aligned_values() -> None:
    """Precision validation passes for aligned price and volume."""
    profile = _profile()
    validate_precision_capability(
        profile=profile, price=Decimal("1.10000"), volume=Decimal("0.02")
    )


def test_validate_rate_limit_capability() -> None:
    """Rate limit validation passes within capability and fails above it."""
    profile = _profile(max_requests_per_second=Decimal(5))
    validate_rate_limit_capability(profile=profile, requested_rate=Decimal(5))
    with pytest.raises(TradingValidationError):
        validate_rate_limit_capability(profile=profile, requested_rate=Decimal(6))


def test_validate_broker_capabilities_aggregate_success() -> None:
    """validate_broker_capabilities passes when every sub-check passes."""
    profile = _profile()
    result = validate_broker_capabilities(
        profile=profile,
        order_type="market",
        filling_mode="IOC",
        price=Decimal("1.10000"),
        volume=Decimal("0.10"),
    )
    assert result.passed is True


def test_validate_broker_capabilities_short_circuits_on_first_failure() -> None:
    """validate_broker_capabilities short-circuits on the first failing check."""
    profile = _profile()
    with pytest.raises(TradingValidationError):
        validate_broker_capabilities(
            profile=profile,
            order_type="unsupported_type",
            filling_mode="IOC",
            price=Decimal("1.10000"),
            volume=Decimal("0.10"),
        )


def test_requires_cancel_on_disconnect_failsafe() -> None:
    """The CoD failsafe is required exactly when native support is absent."""
    unsupported = _profile(supports_cancel_on_disconnect=False)
    supported = _profile(supports_cancel_on_disconnect=True)
    assert requires_cancel_on_disconnect_failsafe(profile=unsupported) is True
    assert requires_cancel_on_disconnect_failsafe(profile=supported) is False
