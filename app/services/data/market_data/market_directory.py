"""Paginated categorized market-directory retrieval."""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime
from typing import Final, cast

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
    unwrap_data_response,
)
from app.services.data.market_data.directory_contracts import (
    MarketDirectory,
    MarketDirectoryRequest,
)
from app.services.data.market_data.directory_projection import enrich_symbols
from app.services.data.market_data.symbol_discovery import list_symbols
from app.services.data.market_data.symbol_metadata import SymbolListRequest, SymbolPage

logger = get_logger(__name__)

_DIRECTORY_CACHE_TTL_SECONDS: Final = 15.0
_DirectoryCacheKey = tuple[str, str | None, str | None, int]
_directory_cache_lock: Final = threading.Lock()
_directory_cache: dict[_DirectoryCacheKey, tuple[float, MarketDirectory]] = {}


def _reset_directory_cache_for_tests() -> None:
    """Clear the in-process directory cache for isolated tests."""
    with _directory_cache_lock:
        _directory_cache.clear()


def _directory_cache_key(request: MarketDirectoryRequest) -> _DirectoryCacheKey:
    """Build one complete directory cache key.

    Args:
        request: Bounded directory request.

    Returns:
        Key containing every result-shaping field.
    """
    return (request.source_id, request.query, request.cursor, request.limit)


def _build_directory_raw(request: MarketDirectoryRequest) -> MarketDirectory:
    """Compose one directory page from symbol and market evidence.

    Args:
        request: Bounded directory request.

    Returns:
        Categorized directory page.
    """
    page = cast(
        "SymbolPage",
        unwrap_data_response(
            list_symbols(
                SymbolListRequest(
                    source_id=request.source_id,
                    query=request.query,
                    cursor=request.cursor,
                    limit=request.limit,
                    request_id=request.request_id,
                )
            ),
            operation="data.market_data.market_directory.list",
            request_id=request.request_id,
        ),
    )
    return MarketDirectory(
        source_id=request.source_id,
        rows=enrich_symbols(
            request.source_id,
            tuple(page.items),
            request.request_id,
        ),
        limit=request.limit,
        next_cursor=page.next_cursor,
        revision=page.revision,
        generated_at=datetime.now(UTC),
        request_id=request.request_id,
    )


def _build_directory_cached(request: MarketDirectoryRequest) -> MarketDirectory:
    """Return a fresh cached page or build one.

    Args:
        request: Bounded directory request.

    Returns:
        Fresh directory page.
    """
    key = _directory_cache_key(request)
    now = time.monotonic()
    with _directory_cache_lock:
        cached = _directory_cache.get(key)
        if cached is not None and now - cached[0] < _DIRECTORY_CACHE_TTL_SECONDS:
            logger.info("Serving cached market-directory page")
            return cached[1].model_copy(update={"request_id": request.request_id})
    directory = _build_directory_raw(request)
    with _directory_cache_lock:
        _directory_cache[key] = (now, directory)
    return directory


def list_market_directory(
    request: MarketDirectoryRequest | None = None,
    *,
    source_id: str | None = None,
    query: str | None = None,
    cursor: str | None = None,
    limit: int | None = None,
    request_id: str | None = None,
) -> StandardResponse[MarketDirectory]:
    """List one categorized market-directory page.

    Args:
        request: Typed directory request.
        source_id: Direct-call source identifier.
        query: Direct-call optional query.
        cursor: Direct-call optional cursor.
        limit: Direct-call page limit.
        request_id: Direct-call trace identifier.

    Returns:
        Standard response carrying the directory page.
    """
    logger.info("Executing public DATA market-directory listing")
    resolved_id = request.request_id if request is not None else request_id

    def _raw() -> MarketDirectory:
        """Resolve and execute one directory request.

        Returns:
            Categorized directory page.

        Raises:
            ValueError: If direct-call required inputs are absent.
        """
        if request is not None:
            resolved = request
        else:
            if source_id is None or limit is None:
                raise ValueError(
                    "source_id and limit are required without a typed request"
                )
            resolved = MarketDirectoryRequest(
                source_id=source_id,
                query=query,
                cursor=cursor,
                limit=limit,
                request_id=request_id if request_id is not None else generate_id("req"),
            )
        return _build_directory_cached(resolved)

    return run_data_operation(
        operation="data.market_data.list_market_directory",
        request_id=resolved_id,
        start_time=data_start_time(),
        raw=_raw,
    )


def build_market_directory_request(
    *,
    source_id: str,
    limit: int = 50,
    query: str | None = None,
    cursor: str | None = None,
    request_id: str | None = None,
) -> MarketDirectoryRequest:
    """Build one validated directory request.

    Args:
        source_id: Owning source identifier.
        limit: Page size.
        query: Optional symbol query.
        cursor: Optional page cursor.
        request_id: Optional trace identifier.

    Returns:
        Validated directory request.
    """
    return MarketDirectoryRequest(
        source_id=source_id,
        limit=limit,
        query=query,
        cursor=cursor,
        request_id=request_id if request_id is not None else generate_id("req"),
    )


__all__ = ("build_market_directory_request", "list_market_directory")
