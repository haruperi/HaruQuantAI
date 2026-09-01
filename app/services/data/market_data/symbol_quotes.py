"""Bounded quote retrieval for an explicit symbol list."""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime
from typing import Final

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.market_data.directory_contracts import (
    MarketDirectory,
    MarketDirectoryRow,
    SymbolsQuoteRequest,
)
from app.services.data.market_data.directory_projection import enrich_symbols

logger = get_logger(__name__)

_QUOTE_CACHE_TTL_SECONDS: Final = 15.0
_QuoteCacheKey = tuple[str, tuple[str, ...]]
_quote_cache_lock: Final = threading.Lock()
_quote_cache: dict[_QuoteCacheKey, tuple[float, tuple[MarketDirectoryRow, ...]]] = {}


def _reset_quote_cache_for_tests() -> None:
    """Clear the in-process quote cache for isolated tests."""
    with _quote_cache_lock:
        _quote_cache.clear()


def _build_quotes_cached(
    request: SymbolsQuoteRequest,
) -> tuple[MarketDirectoryRow, ...]:
    """Return fresh cached rows or build them.

    Args:
        request: Bounded exact-symbol request.

    Returns:
        Categorized rows in caller order.
    """
    key: _QuoteCacheKey = (request.source_id, request.symbols)
    now = time.monotonic()
    with _quote_cache_lock:
        cached = _quote_cache.get(key)
        if cached is not None and now - cached[0] < _QUOTE_CACHE_TTL_SECONDS:
            logger.info("Serving cached explicit-symbol quotes")
            return cached[1]
    rows = enrich_symbols(request.source_id, request.symbols, request.request_id)
    with _quote_cache_lock:
        _quote_cache[key] = (now, rows)
    return rows


def get_symbols_quotes(
    request: SymbolsQuoteRequest,
) -> StandardResponse[MarketDirectory]:
    """Return quotes for exactly the caller-declared symbols.

    Args:
        request: Bounded exact-symbol request.

    Returns:
        Standard response carrying categorized quote rows.
    """
    logger.info("Executing public DATA explicit-symbol quote listing")

    def _raw() -> MarketDirectory:
        """Build one exact-symbol quote page.

        Returns:
            Quote rows in caller order.
        """
        return MarketDirectory(
            source_id=request.source_id,
            rows=_build_quotes_cached(request),
            limit=len(request.symbols),
            next_cursor=None,
            revision="1.0.0",
            generated_at=datetime.now(UTC),
            request_id=request.request_id,
        )

    return run_data_operation(
        operation="data.market_data.get_symbols_quotes",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=_raw,
    )


def build_symbols_quote_request(
    *,
    source_id: str,
    symbols: tuple[str, ...],
    request_id: str | None = None,
) -> SymbolsQuoteRequest:
    """Build one validated exact-symbol request.

    Args:
        source_id: Owning source identifier.
        symbols: Symbols in requested order.
        request_id: Optional trace identifier.

    Returns:
        Validated exact-symbol request.
    """
    return SymbolsQuoteRequest(
        source_id=source_id,
        symbols=symbols,
        request_id=request_id if request_id is not None else generate_id("req"),
    )


__all__ = ("build_symbols_quote_request", "get_symbols_quotes")
