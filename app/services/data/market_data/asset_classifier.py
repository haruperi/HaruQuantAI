r"""Pure asset-class classification for market-directory rows.

Market-directory consumers group broker symbols into six canonical categories
(``Forex``, ``Commodities``, ``Indices``, ``Stocks``, ``ETFs``,
``Cryptocurrencies``). Broker-native symbol metadata does not carry a field
that maps cleanly onto these categories: for MT5 the authoritative
``SymbolMetadata.asset_class`` is the literal product profile (``"mt5"``),
while the venue's hierarchical grouping path (e.g. ``"Forex\\Majors\\EURUSD"``)
survives into ``SymbolMetadata.path`` and is the only reliable classifier input.

This module is deliberately pure and stateless: it performs no I/O, resolves
no identity, and contacts no source. It owns only the mapping from broker
grouping evidence to one of the seven supported display tokens (the six
categories plus ``Other`` for anything it cannot place). Keeping it out of the
route layer and the broker adapter preserves the Data-owned business rule and
lets the API gateway stay a pure delegator.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

from app.utils import get_logger

logger = get_logger(__name__)

# Canonical directory categories in stable response order. ``Other`` is the
# internal catch-all for symbols that cannot be classified confidently.
FOREX: Final = "Forex"
COMMODITIES: Final = "Commodities"
INDICES: Final = "Indices"
STOCKS: Final = "Stocks"
ETFS: Final = "ETFs"
CRYPTOCURRENCIES: Final = "Cryptocurrencies"
OTHER: Final = "Other"

DISPLAY_ASSET_CLASSES: Final = (
    FOREX,
    COMMODITIES,
    INDICES,
    STOCKS,
    ETFS,
    CRYPTOCURRENCIES,
)

# Known physical-metal spot symbols that MT5 groups under Forex but that the
# directory consumers classify as Commodities. These are the common spot contracts;
# the list is intentionally exhaustive per instrument, not pattern-based, to
# avoid misclassifying a genuine FX pair that happens to contain "XAU".
# Entries are upper-cased because ``_classify_by_symbol`` compares the
# upper-cased symbol against this set.
_METAL_SPOT_SYMBOLS: Final = frozenset(
    {
        "XAUUSD",
        "XAUUSDM",
        "XAUUSD.R",
        "XAUUSD.MICRO",  # Gold
        "XAGUSD",
        "XAGUSDM",
        "XAGUSD.R",  # Silver
        "XPTUSD",  # Platinum
        "XPDUSD",  # Palladium (MT5 casing varies by feed)
    }
)

# Substrings of a broker grouping path that indicate each display category.
# Matched case-insensitively against any backslash/forward-slash segment.
_PATH_KEYWORDS: Final = MappingProxyType(
    {
        "forex": FOREX,
        "fx": FOREX,
        "curr": FOREX,  # "Currencies"
        "metal": COMMODITIES,
        "commod": COMMODITIES,
        "energy": COMMODITIES,
        "oil": COMMODITIES,
        "petrol": COMMODITIES,
        "index": INDICES,
        "indices": INDICES,
        "cash inde": INDICES,  # "Cash Indexes"
        "stock": STOCKS,
        "share": STOCKS,
        "equit": STOCKS,
        "etf": ETFS,
        "crypto": CRYPTOCURRENCIES,
    }
)

# Quote-currency suffixes that identify a retail FX pair when the grouping
# path is unavailable or uninformative. A six-character symbol whose last
# three characters match one of these is treated as Forex.
_FX_QUOTE_CURRENCIES: Final = frozenset({"USD", "EUR", "GBP", "JPY", "CHF"})
# Standard retail FX-pair symbol length (e.g. "EURUSD").
_FX_SYMBOL_LENGTH: Final = 6


def _clean_segments(value: str | None) -> tuple[str, ...]:
    r"""Split a grouping path into normalized lowercased segments.

    MT5 grouping paths use a Windows-style backslash separator
    (``"Forex\\Majors\\EURUSD"``); some feeds use a forward slash. This helper
    accepts either, drops empty segments, and lowercases for matching.

    Args:
        value: Raw grouping path, or ``None`` when the broker omitted it.

    Returns:
        Tuple of non-empty trimmed lowercased segments.
    """
    if not value:
        return ()
    normalized = value.replace("\\", "/").replace("|", "/")
    return tuple(
        segment.strip().lower() for segment in normalized.split("/") if segment.strip()
    )


def _classify_by_symbol(symbol: str | None) -> str | None:
    """Classify using symbol-name heuristics as a fallback.

    Args:
        symbol: Broker-native symbol string, or ``None``.

    Returns:
        A display category when the symbol matches a known pattern, else None.
    """
    if not symbol:
        return None
    upper = symbol.upper()
    if upper in _METAL_SPOT_SYMBOLS:
        return COMMODITIES
    if upper.startswith(("BTC", "ETH", "LTC")):
        # Crypto spot/derivatives (BTCUSD, ETHUSD, BTCETH...). Checked before
        # the FX heuristic so BTCJPY is not mistaken for a yen pair.
        return CRYPTOCURRENCIES
    if (
        len(upper) == _FX_SYMBOL_LENGTH
        and upper[3:6] in _FX_QUOTE_CURRENCIES
        and upper[0:3].isalpha()
    ):
        return FOREX
    return None


def _classify_by_path(path: str | None) -> str | None:
    """Inspect path segments for matching keywords.

    Args:
        path: Optional broker grouping path.

    Returns:
        Matched display asset class, or ``None``.
    """
    segments = _clean_segments(path)
    for segment in segments:
        for keyword, asset_class in _PATH_KEYWORDS.items():
            if keyword in segment:
                return asset_class
    return None


def classify_symbol(
    path: str | None,
    symbol: str | None,
    currency_base: str | None = None,
    currency_profit: str | None = None,
) -> str:
    r"""Map broker grouping evidence to one display asset class.

    The classifier prefers the venue grouping path (most reliable), extracting
    the leading directory segment (e.g. ``"Forex"`` from ``"Forex\\EURJPY"``)
    when present, then falls back to symbol-name heuristics. Physical metals
    and cryptocurrencies retain safety overrides so spot metals (e.g. ``XAUUSD``)
    and cryptos are never mis-bucketed if a broker places them under an FX folder.

    Args:
        path: Broker grouping path (e.g. ``"Forex\\EURJPY"``), or None.
        symbol: Broker-native symbol string (e.g. ``"EURJPY"``), or None.
        currency_base: Optional base currency hint.
        currency_profit: Optional quote/profit currency hint.

    Returns:
        One of the seven tokens in ``DISPLAY_ASSET_CLASSES`` or ``OTHER``.
    """
    del currency_base, currency_profit  # forward-compat inputs, not yet needed

    if symbol:
        upper = symbol.upper()
        if upper in _METAL_SPOT_SYMBOLS:
            return COMMODITIES
        if upper.startswith(("BTC", "ETH", "LTC")):
            return CRYPTOCURRENCIES

    path_class = _classify_by_path(path)
    if path_class is not None:
        return path_class

    symbol_class = _classify_by_symbol(symbol)
    if symbol_class is not None:
        return symbol_class

    return OTHER


__all__ = (
    "COMMODITIES",
    "CRYPTOCURRENCIES",
    "DISPLAY_ASSET_CLASSES",
    "ETFS",
    "FOREX",
    "INDICES",
    "OTHER",
    "STOCKS",
    "classify_symbol",
)
