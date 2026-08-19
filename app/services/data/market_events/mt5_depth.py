"""Canonical multi-symbol Depth-of-Market reads sourced from the MT5 TCP bridge."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, field_validator

from app.services.data.contracts import DataError

_MAX_SYMBOLS = 200
_MAX_SYMBOL_LENGTH = 128
_STALE_AFTER_SECONDS = 5.0
_FIRST_EVENT_TIMEOUT_SECONDS = 5.0


class _DepthRequest(BaseModel):
    """Validated internal request for a multi-symbol Depth-of-Market stream."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    symbols: tuple[str, ...]
    request_id: str
    resume_after: int | None = None

    @field_validator("symbols")
    @classmethod
    def _validate_symbols(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Normalize unique broker-native symbols while preserving order.

        Args:
            value: Candidate symbol tuple.

        Returns:
            Trimmed, order-preserving, unique symbol tuple.

        Raises:
            ValueError: If the count is out of bounds, an entry is empty or
                too long, or a symbol repeats.
        """
        normalized = tuple(symbol.strip() for symbol in value)
        if not 1 <= len(normalized) <= _MAX_SYMBOLS:
            raise ValueError("depth symbol count is outside bounds")
        if any(not symbol or len(symbol) > _MAX_SYMBOL_LENGTH for symbol in normalized):
            raise ValueError("depth symbols must be bounded non-empty strings")
        if len(normalized) != len(set(normalized)):
            raise ValueError("depth symbols must be unique")
        return normalized

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Require one trimmed request identity.

        Args:
            value: Candidate request identifier.

        Returns:
            The unchanged trimmed request identifier.

        Raises:
            ValueError: If the value is empty or carries untrimmed whitespace.
        """
        if not value or value != value.strip():
            raise ValueError("request_id must be trimmed")
        return value

    @field_validator("resume_after")
    @classmethod
    def _validate_resume(cls, value: int | None) -> int | None:
        """Require a non-negative optional producer sequence.

        Args:
            value: Candidate resume sequence, or ``None``.

        Returns:
            The unchanged non-negative resume sequence, or ``None``.

        Raises:
            ValueError: If the value is negative.
        """
        if value is not None and value < 0:
            raise ValueError("resume_after must be non-negative")
        return value


class _DepthEvent(BaseModel):
    """Canonical Data event carrying one filtered atomic Depth-of-Market read."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    sequence: int
    occurred_at: datetime
    books: tuple[Mapping[str, object], ...]
    stale: bool
    gap: int
    request_id: str
    source_id: str
    errors: tuple[Mapping[str, object], ...]


def build_market_depth_stream_request(**values: object) -> object:
    """Build a bounded multi-symbol MT5 Depth-of-Market request.

    Args:
        values: Request fields accepted by the internal contract.

    Returns:
        Opaque validated request for ``stream_market_depth``.
    """
    return _DepthRequest.model_validate(values)


def _normalized_levels(
    raw_levels: tuple[Mapping[str, object], ...],
) -> tuple[Mapping[str, object], ...]:
    """Build one side's validated bounded price levels.

    Args:
        raw_levels: Broker-ordered levels already bounded by the gateway.

    Returns:
        Immutable tuple of normalized price/volume levels.
    """
    return tuple(
        {
            "price": cast("Decimal", level["price"]),
            "volume": cast("Decimal", level["volume"]),
        }
        for level in raw_levels
    )


async def _next_book(
    source: AsyncIterator[Mapping[str, object]],
) -> Mapping[str, object] | None:
    """Read the next upstream book frame, treating exhaustion as ``None``.

    Args:
        source: Active gateway book iterator.

    Returns:
        The next raw book frame, or ``None`` once the source is exhausted.
    """
    try:
        return await anext(source)
    except StopAsyncIteration:
        return None


async def stream_market_depth(request: object) -> AsyncIterator[object]:
    """Yield atomic one-second Depth-of-Market reads filtered to requested symbols.

    A symbol reported as an explicit book error upstream (its broker publishes
    no book for it) is surfaced in ``errors`` and carries no synthesized
    levels; a subscribed symbol with zero current resting levels is a genuine
    empty book, not an error.

    The wait for the first delivered event is bounded. Upstream silence, or
    book frames that never mention a requested symbol, fail the stream
    explicitly rather than holding the consumer open indefinitely. Once an
    event has been delivered the stream follows the upstream cadence again.

    Args:
        request: Value returned by ``build_market_depth_stream_request``.

    Yields:
        Canonical immutable depth events.

    Raises:
        DataError: If the request type or upstream book read is invalid, or if
            no requested symbol produces an event within the first-read bound.
    """
    from app.services.brokers import (
        acquire_metatrader_snapshot_symbols,
        release_metatrader_snapshot_symbols,
        stream_metatrader_book_snapshots,
    )

    if not isinstance(request, _DepthRequest):
        raise DataError("INVALID_INPUT", safe_details={"contract": "depth"})
    requested = set(request.symbols)
    try:
        consumer_id = await acquire_metatrader_snapshot_symbols(request.symbols)
    except (TimeoutError, ValueError) as error:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "mt5_symbol_demand"},
            request_id=request.request_id,
        ) from error
    source = stream_metatrader_book_snapshots()
    deadline = asyncio.get_running_loop().time() + _FIRST_EVENT_TIMEOUT_SECONDS
    delivered = False
    try:
        while True:
            try:
                if delivered:
                    book = await _next_book(source)
                else:
                    async with asyncio.timeout_at(deadline):
                        book = await _next_book(source)
            except TimeoutError as error:
                raise DataError(
                    "SOURCE_UNAVAILABLE",
                    safe_details={"operation": "mt5_depth_first_read"},
                    request_id=request.request_id,
                ) from error
            if book is None:
                return
            sequence = cast("int", book["sequence"])
            if request.resume_after is not None and sequence <= request.resume_after:
                continue
            received_at = cast("datetime", book["received_at"])
            raw_books = cast("tuple[Mapping[str, Any], ...]", book["books"])
            filtered = tuple(
                {
                    "symbol": str(entry["symbol"]),
                    "book_depth": int(cast("int", entry["book_depth"])),
                    "bids": _normalized_levels(
                        cast("tuple[Mapping[str, object], ...]", entry["bids"])
                    ),
                    "asks": _normalized_levels(
                        cast("tuple[Mapping[str, object], ...]", entry["asks"])
                    ),
                }
                for entry in raw_books
                if entry["symbol"] in requested
            )
            raw_errors = cast(
                "tuple[Mapping[str, object], ...]",
                book.get("errors", ()),
            )
            filtered_errors = tuple(
                error for error in raw_errors if error["symbol"] in requested
            )
            if not filtered and not filtered_errors:
                continue
            delivered = True
            age_seconds = max(0.0, (datetime.now(UTC) - received_at).total_seconds())
            yield _DepthEvent(
                sequence=sequence,
                occurred_at=received_at,
                books=filtered,
                stale=age_seconds > _STALE_AFTER_SECONDS,
                gap=cast("int", book.get("gap", 0)),
                request_id=request.request_id,
                source_id=cast("str", book["source_id"]),
                errors=filtered_errors,
            )
    finally:
        await release_metatrader_snapshot_symbols(consumer_id)


__all__ = ["build_market_depth_stream_request", "stream_market_depth"]
