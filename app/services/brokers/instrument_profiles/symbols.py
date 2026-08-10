"""Symbol identity reads for Instrument and Venue Profiles."""

from __future__ import annotations

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


def resolve_broker_provider_symbol(
    provider_code: str, symbol_id: str, *, request_id: str
) -> object:
    """Resolve the current provider symbol for a canonical instrument.

    Args:
        provider_code: Canonical provider identifier.
        symbol_id: Canonical instrument identifier.
        request_id: Canonical caller request identifier.

    Returns:
        Data-owned standard transaction response carrying at most one row.

    Raises:
        ValueError: If an identifier is empty or unbounded.
    """
    from app.services.brokers.persistence import read_provider_symbol

    return read_provider_symbol(
        _text(provider_code, "provider_code"),
        _text(symbol_id, "symbol_id"),
        request_id=_text(request_id, "request_id"),
    )


def resolve_broker_canonical_symbol(
    provider_code: str, provider_symbol: str, *, request_id: str
) -> object:
    """Resolve the canonical instrument for a current provider symbol.

    Args:
        provider_code: Canonical provider identifier.
        provider_symbol: Provider-native symbol identifier.
        request_id: Canonical caller request identifier.

    Returns:
        Data-owned standard transaction response carrying at most one row.

    Raises:
        ValueError: If an identifier is empty or unbounded.
    """
    from app.services.brokers.persistence import read_canonical_symbol

    return read_canonical_symbol(
        _text(provider_code, "provider_code"),
        _text(provider_symbol, "provider_symbol"),
        request_id=_text(request_id, "request_id"),
    )


def resolve_broker_provider_symbol_as_of(
    provider_code: str,
    symbol_id: str,
    as_of: str,
    *,
    request_id: str,
) -> object:
    """Resolve the provider symbol valid at one historical instant.

    Args:
        provider_code: Canonical provider identifier.
        symbol_id: Canonical instrument identifier.
        as_of: ISO-8601 point-in-time boundary.
        request_id: Canonical caller request identifier.

    Returns:
        Data-owned standard transaction response carrying at most one row.

    Raises:
        ValueError: If an identifier or time value is empty or unbounded.
    """
    from app.services.brokers.persistence import read_provider_symbol_as_of

    return read_provider_symbol_as_of(
        _text(provider_code, "provider_code"),
        _text(symbol_id, "symbol_id"),
        _text(as_of, "as_of"),
        request_id=_text(request_id, "request_id"),
    )


__all__ = [
    "resolve_broker_canonical_symbol",
    "resolve_broker_provider_symbol",
    "resolve_broker_provider_symbol_as_of",
]
