"""Canonical multi-symbol snapshots sourced from the MT5 TCP bridge."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, field_validator

from app.services.brokers import (
    acquire_metatrader_snapshot_symbols,
    release_metatrader_snapshot_symbols,
    stream_metatrader_snapshots,
)
from app.services.data.contracts import DataError

_MAX_SYMBOLS = 200
_MAX_SYMBOL_LENGTH = 128
_STALE_AFTER_SECONDS = 5.0


class _SnapshotRequest(BaseModel):
    """Validated internal request for a multi-symbol snapshot stream."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    symbols: tuple[str, ...]
    request_id: str
    resume_after: int | None = None

    @field_validator("symbols")
    @classmethod
    def _validate_symbols(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Normalize unique broker-native symbols while preserving order.

        Args:
            value: Requested exact provider symbols.

        Returns:
            Trimmed unique symbol tuple.

        Raises:
            ValueError: If count, text bounds, or uniqueness is invalid.
        """
        normalized = tuple(symbol.strip() for symbol in value)
        if not 1 <= len(normalized) <= _MAX_SYMBOLS:
            raise ValueError("snapshot symbol count is outside bounds")
        if any(not symbol or len(symbol) > _MAX_SYMBOL_LENGTH for symbol in normalized):
            raise ValueError("snapshot symbols must be bounded non-empty strings")
        if len(normalized) != len(set(normalized)):
            raise ValueError("snapshot symbols must be unique")
        return normalized

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Require one trimmed request identity.

        Args:
            value: Requested correlation identity.

        Returns:
            Validated request identity.

        Raises:
            ValueError: If the identity is empty or untrimmed.
        """
        if not value or value != value.strip():
            raise ValueError("request_id must be trimmed")
        return value

    @field_validator("resume_after")
    @classmethod
    def _validate_resume(cls, value: int | None) -> int | None:
        """Require a non-negative optional producer sequence.

        Args:
            value: Optional last-consumed producer sequence.

        Returns:
            Validated optional sequence.

        Raises:
            ValueError: If the sequence is negative.
        """
        if value is not None and value < 0:
            raise ValueError("resume_after must be non-negative")
        return value


class _SnapshotEvent(BaseModel):
    """Canonical Data event carrying one filtered atomic snapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    sequence: int
    occurred_at: datetime
    quotes: tuple[Mapping[str, object], ...]
    stale: bool
    gap: int
    request_id: str
    source_id: str
    errors: tuple[Mapping[str, object], ...]


def build_market_snapshot_stream_request(**values: object) -> object:
    """Build a bounded multi-symbol MT5 snapshot request.

    Args:
        values: Request fields accepted by the internal contract.

    Returns:
        Opaque validated request for ``stream_market_snapshots``.
    """
    return _SnapshotRequest.model_validate(values)


async def stream_market_snapshots(request: object) -> AsyncIterator[object]:
    """Yield atomic one-second snapshots filtered to requested symbols.

    Args:
        request: Value returned by ``build_market_snapshot_stream_request``.

    Yields:
        Canonical immutable snapshot events.

    Raises:
        DataError: If the request type or upstream snapshot is invalid.
    """
    if not isinstance(request, _SnapshotRequest):
        raise DataError("INVALID_INPUT", safe_details={"contract": "snapshot"})
    requested = set(request.symbols)
    try:
        consumer_id = await acquire_metatrader_snapshot_symbols(request.symbols)
    except (TimeoutError, ValueError) as error:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "mt5_symbol_demand"},
            request_id=request.request_id,
        ) from error
    try:
        async for snapshot in stream_metatrader_snapshots():
            sequence = cast("int", snapshot["sequence"])
            if request.resume_after is not None and sequence <= request.resume_after:
                continue
            received_at = cast("datetime", snapshot["received_at"])
            raw_quotes = cast("tuple[Mapping[str, Any], ...]", snapshot["quotes"])
            filtered = tuple(
                {
                    "symbol": str(quote["symbol"]),
                    "time": datetime.fromtimestamp(
                        cast("int", quote["time_msc"]) / 1_000,
                        tz=UTC,
                    ),
                    "bid": cast("Decimal", quote["bid"]),
                    "ask": cast("Decimal", quote["ask"]),
                    "last": cast("Decimal | None", quote["last"]),
                    "spread": cast("Decimal", quote["ask"])
                    - cast("Decimal", quote["bid"]),
                    "volume": cast("int", quote["volume"]),
                    "volume_real": cast("Decimal", quote["volume_real"]),
                    "flags": cast("int", quote["flags"]),
                    "digits": cast("int", quote["digits"]),
                }
                for quote in raw_quotes
                if quote["symbol"] in requested
            )
            if not filtered:
                continue
            newest_quote = max(cast("datetime", quote["time"]) for quote in filtered)
            age_seconds = max(0.0, (datetime.now(UTC) - newest_quote).total_seconds())
            raw_errors = cast(
                "tuple[Mapping[str, object], ...]",
                snapshot.get("errors", ()),
            )
            yield _SnapshotEvent(
                sequence=sequence,
                occurred_at=received_at,
                quotes=filtered,
                stale=age_seconds > _STALE_AFTER_SECONDS,
                gap=cast("int", snapshot.get("gap", 0)),
                request_id=request.request_id,
                source_id=cast("str", snapshot["source_id"]),
                errors=tuple(
                    error for error in raw_errors if error["symbol"] in requested
                ),
            )
    finally:
        await release_metatrader_snapshot_symbols(consumer_id)


__all__ = ["build_market_snapshot_stream_request", "stream_market_snapshots"]
