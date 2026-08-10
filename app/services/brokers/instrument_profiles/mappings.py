"""Instrument-profile operations for bitemporal symbol mappings."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.utils import generate_id, get_logger, utc_now

logger = get_logger(__name__)
_MAX_TEXT_LENGTH = 256


def _text(value: str, field_name: str) -> str:
    """Validate one required bounded text value.

    Args:
        value: Candidate text.
        field_name: Stable field label for validation failures.

    Returns:
        Stripped non-empty text.

    Raises:
        ValueError: If the value is empty or exceeds 256 characters.
    """
    normalized = value.strip()
    if not normalized or len(normalized) > _MAX_TEXT_LENGTH:
        msg = f"{field_name} must contain 1..256 characters"
        raise ValueError(msg)
    return normalized


def register_broker_symbol_mapping(
    provider_code: str,
    symbol_id: str,
    provider_symbol: str,
    *,
    request_id: str,
    effective_from: str,
    contract_size: Decimal | str = Decimal(1),
    digits_override: int | None = None,
    correlation_id: str = "",
) -> object:
    """Register one active provider-to-canonical symbol mapping.

    Args:
        provider_code: Canonical provider identifier.
        symbol_id: Canonical instrument identifier.
        provider_symbol: Provider-native symbol identifier.
        request_id: Canonical caller request identifier.
        effective_from: Inclusive ISO-8601 validity start.
        contract_size: Positive provider contract-size multiplier.
        digits_override: Optional non-negative provider precision.
        correlation_id: Optional bounded correlation identifier.

    Returns:
        Data-owned standard transaction response.

    Raises:
        ValueError: If identifiers, contract size, or precision are invalid.
    """
    try:
        size = Decimal(str(contract_size))
    except InvalidOperation as error:
        raise ValueError("contract_size must be decimal-compatible") from error
    if not size.is_finite() or size <= 0:
        raise ValueError("contract_size must be finite and positive")
    if digits_override is not None and digits_override < 0:
        raise ValueError("digits_override must be non-negative")
    now = utc_now().isoformat()
    parameters = (
        generate_id("led"),
        _text(provider_code, "provider_code"),
        _text(symbol_id, "symbol_id"),
        _text(provider_symbol, "provider_symbol"),
        str(size),
        digits_override,
        1,
        _text(effective_from, "effective_from"),
        None,
        _text(request_id, "request_id"),
        correlation_id.strip(),
        now,
        now,
    )
    logger.info("Registering validated Brokers symbol mapping")
    from app.services.brokers.persistence import create_symbol_map_record

    return create_symbol_map_record(parameters, request_id=request_id)


def close_broker_symbol_mapping(
    provider_code: str,
    symbol_id: str,
    effective_to: str,
    *,
    request_id: str,
) -> object:
    """Close the current mapping without rewriting its history.

    Args:
        provider_code: Canonical provider identifier.
        symbol_id: Canonical instrument identifier.
        effective_to: Exclusive ISO-8601 validity end.
        request_id: Canonical caller request identifier.

    Returns:
        Data-owned standard transaction response.

    Raises:
        ValueError: If an identifier or time value is empty or unbounded.
    """
    from app.services.brokers.persistence import close_symbol_mapping

    return close_symbol_mapping(
        _text(effective_to, "effective_to"),
        utc_now().isoformat(),
        _text(provider_code, "provider_code"),
        _text(symbol_id, "symbol_id"),
        request_id=_text(request_id, "request_id"),
    )


def disable_broker_symbol_mapping(map_id: str, *, request_id: str) -> object:
    """Disable one mapping without deleting historical evidence.

    Args:
        map_id: Stable mapping identifier.
        request_id: Canonical caller request identifier.

    Returns:
        Data-owned standard transaction response.

    Raises:
        ValueError: If an identifier is empty or unbounded.
    """
    from app.services.brokers.persistence import disable_symbol_mapping

    return disable_symbol_mapping(
        utc_now().isoformat(),
        _text(map_id, "map_id"),
        request_id=_text(request_id, "request_id"),
    )


__all__ = [
    "close_broker_symbol_mapping",
    "disable_broker_symbol_mapping",
    "register_broker_symbol_mapping",
]
