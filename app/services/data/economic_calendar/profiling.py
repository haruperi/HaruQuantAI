"""Symbol-to-economic-event mapping profiles for FEAT-DATA-11.

A `SymbolEventProfile` declares which currencies and countries are material to
a tradable symbol. Calendar events whose ``currency`` or ``country`` intersects
the profile set are relevant to that symbol. Profiles are immutable and
declared as the canonical ``SYMBOL_EVENT_PROFILES`` registry so that strategy,
risk, and Storage code reuse one mapping.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from app.services.data.contracts import DataError


@dataclass(frozen=True, slots=True)
class SymbolEventProfile:
    """Declares the currencies and countries material to one symbol.

    Attributes:
        symbol: Canonical tradable symbol (e.g. ``"EURUSD"``).
        currencies: ISO-4217 currency codes that move this symbol.
        countries: ISO-3166-1 alpha-2 country codes that move this symbol.
    """

    symbol: str
    currencies: frozenset[str]
    countries: frozenset[str]


SYMBOL_EVENT_PROFILES: Final[Mapping[str, SymbolEventProfile]] = MappingProxyType(
    {
        "EURUSD": SymbolEventProfile(
            symbol="EURUSD",
            currencies=frozenset({"EUR", "USD"}),
            countries=frozenset({"EU", "US"}),
        ),
        "GBPJPY": SymbolEventProfile(
            symbol="GBPJPY",
            currencies=frozenset({"GBP", "JPY"}),
            countries=frozenset({"GB", "JP"}),
        ),
        "XAUUSD": SymbolEventProfile(
            symbol="XAUUSD",
            currencies=frozenset({"USD"}),
            countries=frozenset({"US"}),
        ),
        "NAS100": SymbolEventProfile(
            symbol="NAS100",
            currencies=frozenset({"USD"}),
            countries=frozenset({"US"}),
        ),
        "GER40": SymbolEventProfile(
            symbol="GER40",
            currencies=frozenset({"EUR"}),
            countries=frozenset({"DE", "EU"}),
        ),
    }
)


def get_symbol_event_profile(symbol: str) -> SymbolEventProfile:
    """Return the canonical profile for ``symbol`` or fail closed.

    Args:
        symbol: Canonical tradable symbol.

    Returns:
        The matching immutable profile.

    Raises:
        DataError: If the symbol has no registered profile.
    """
    profile = SYMBOL_EVENT_PROFILES.get(symbol)
    if profile is None:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "symbol"})
    return profile


__all__ = ["SYMBOL_EVENT_PROFILES", "SymbolEventProfile", "get_symbol_event_profile"]
