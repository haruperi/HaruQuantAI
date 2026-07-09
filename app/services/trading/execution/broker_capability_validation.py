"""Broker adapter capability validation primitives.

This module validates order types, filling modes, price/volume precision,
and client-side throughput against a declared broker adapter capability
profile before broker execution, failing closed on any mismatch
(TRD-FR-115). It also reports whether the broker adapter natively supports
Cancel-on-Disconnect so callers know whether the local heartbeat failsafe
must run (TRD-FR-116); actually running that heartbeat loop and triggering
the emergency sweep is the future responsibility of
``runtime/session_manager.py``.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field, model_validator

from app.services.trading.contracts import TradingContract
from app.services.trading.security.error_mapping import TradingValidationError
from app.utils.logger import logger


class BrokerCapabilityProfile(TradingContract):
    """Declared broker adapter capability contract.

    Attributes:
        provider: Broker provider name.
        supported_order_types: Order type identifiers the adapter accepts
            (e.g. ``market``, ``limit``, ``stop``, ``stop_limit``).
        supported_filling_modes: Filling mode identifiers the adapter
            accepts (e.g. ``IOC``, ``FOK``, ``RETURN``).
        price_precision_digits: Maximum supported price decimal digits.
        volume_precision_step: Minimum supported volume increment.
        max_requests_per_second: Maximum sustained client-side request rate.
        supports_cancel_on_disconnect: Whether the adapter natively supports
            Cancel-on-Disconnect.
        supports_native_oco: Whether the adapter natively supports OCO order
            groups.
        supports_sl_tp_attachment: Whether the adapter supports attaching
            SL/TP on order open.
    """

    provider: str
    supported_order_types: tuple[str, ...]
    supported_filling_modes: tuple[str, ...]
    price_precision_digits: int = Field(ge=0)
    volume_precision_step: Decimal = Field(gt=0)
    max_requests_per_second: Decimal = Field(gt=0)
    supports_cancel_on_disconnect: bool = False
    supports_native_oco: bool = False
    supports_sl_tp_attachment: bool = True

    @model_validator(mode="after")
    def validate_profile(self) -> BrokerCapabilityProfile:
        """Validate the capability profile is non-empty and well-formed.

        Returns:
            BrokerCapabilityProfile: Validated capability profile.

        Raises:
            ValueError: If ``provider`` is blank or a supported-set field is
                empty.
        """
        logger.info("Validating broker capability profile for {}.", self.provider)
        if not self.provider.strip():
            raise ValueError("provider must be non-empty.")
        if not self.supported_order_types:
            raise ValueError("supported_order_types must not be empty.")
        if not self.supported_filling_modes:
            raise ValueError("supported_filling_modes must not be empty.")
        return self


class CapabilityCheckResult(TradingContract):
    """Aggregate broker capability validation outcome.

    Attributes:
        passed: Whether every capability check passed.
    """

    passed: bool


def validate_order_type_capability(
    *,
    profile: BrokerCapabilityProfile,
    order_type: str,
) -> None:
    """Validate that the adapter supports the requested order type.

    Args:
        profile: Declared broker adapter capability profile.
        order_type: Requested order type identifier.

    Raises:
        TradingValidationError: If the order type is unsupported.
    """
    logger.info(
        "Validating order type capability {} for {}.", order_type, profile.provider
    )
    if order_type not in profile.supported_order_types:
        raise TradingValidationError(
            "Broker adapter does not support this order type.",
            details={"provider": profile.provider, "order_type": order_type},
        )
    logger.debug("Order type {} is supported by {}.", order_type, profile.provider)


def validate_filling_mode_capability(
    *,
    profile: BrokerCapabilityProfile,
    filling_mode: str,
) -> None:
    """Validate that the adapter supports the requested filling mode.

    Args:
        profile: Declared broker adapter capability profile.
        filling_mode: Requested filling mode identifier.

    Raises:
        TradingValidationError: If the filling mode is unsupported.
    """
    logger.info(
        "Validating filling mode capability {} for {}.",
        filling_mode,
        profile.provider,
    )
    if filling_mode not in profile.supported_filling_modes:
        raise TradingValidationError(
            "Broker adapter does not support this filling mode.",
            details={"provider": profile.provider, "filling_mode": filling_mode},
        )
    logger.debug("Filling mode {} is supported by {}.", filling_mode, profile.provider)


def validate_precision_capability(
    *,
    profile: BrokerCapabilityProfile,
    price: Decimal,
    volume: Decimal,
) -> None:
    """Validate price and volume precision against adapter capability limits.

    Args:
        profile: Declared broker adapter capability profile.
        price: Requested order price.
        volume: Requested order volume.

    Raises:
        TradingValidationError: If price or volume precision exceeds the
            adapter's supported limits.
    """
    logger.info("Validating precision capability for {}.", profile.provider)
    tick = Decimal(1).scaleb(-profile.price_precision_digits)
    if price.quantize(tick) != price:
        raise TradingValidationError(
            "Price precision exceeds broker adapter capability.",
            details={
                "provider": profile.provider,
                "price": str(price),
                "price_precision_digits": profile.price_precision_digits,
            },
        )
    if volume % profile.volume_precision_step != 0:
        raise TradingValidationError(
            "Volume precision exceeds broker adapter capability.",
            details={
                "provider": profile.provider,
                "volume": str(volume),
                "volume_precision_step": str(profile.volume_precision_step),
            },
        )
    logger.debug("Precision capability validation passed for {}.", profile.provider)


def validate_rate_limit_capability(
    *,
    profile: BrokerCapabilityProfile,
    requested_rate: Decimal,
) -> None:
    """Validate that requested throughput fits the adapter's rate capability.

    Args:
        profile: Declared broker adapter capability profile.
        requested_rate: Requested sustained requests-per-second rate.

    Raises:
        TradingValidationError: If the requested rate exceeds capability.
    """
    logger.info("Validating rate limit capability for {}.", profile.provider)
    if requested_rate > profile.max_requests_per_second:
        raise TradingValidationError(
            "Requested rate exceeds broker adapter capability.",
            details={
                "provider": profile.provider,
                "requested_rate": str(requested_rate),
                "max_requests_per_second": str(profile.max_requests_per_second),
            },
        )
    logger.debug("Rate limit capability validation passed for {}.", profile.provider)


def validate_broker_capabilities(
    *,
    profile: BrokerCapabilityProfile,
    order_type: str,
    filling_mode: str,
    price: Decimal,
    volume: Decimal,
) -> CapabilityCheckResult:
    """Validate every adapter capability contract before broker execution.

    Runs order type, filling mode, and precision checks in sequence,
    short-circuiting on the first failure (TRD-FR-115).

    Args:
        profile: Declared broker adapter capability profile.
        order_type: Requested order type identifier.
        filling_mode: Requested filling mode identifier.
        price: Requested order price.
        volume: Requested order volume.

    Returns:
        CapabilityCheckResult: Passing aggregate result.

    Raises:
        TradingValidationError: If any capability check fails.
    """
    logger.info("Validating broker capabilities for provider {}.", profile.provider)
    validate_order_type_capability(profile=profile, order_type=order_type)
    validate_filling_mode_capability(profile=profile, filling_mode=filling_mode)
    validate_precision_capability(profile=profile, price=price, volume=volume)
    logger.debug("Broker capability validation passed for {}.", profile.provider)
    return CapabilityCheckResult(passed=True)


def requires_cancel_on_disconnect_failsafe(*, profile: BrokerCapabilityProfile) -> bool:
    """Return whether the local Cancel-on-Disconnect failsafe must run.

    Args:
        profile: Declared broker adapter capability profile.

    Returns:
        bool: True when the adapter lacks native Cancel-on-Disconnect
        support and a local heartbeat failsafe is required (TRD-FR-116).
    """
    logger.info("Checking Cancel-on-Disconnect capability for {}.", profile.provider)
    return not profile.supports_cancel_on_disconnect
