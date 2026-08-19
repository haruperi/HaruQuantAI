"""One-second MT5 tick snapshots for Data-owned real-time streams."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from app.services.data.contracts import DataError, TickRecord
from app.utils import get_logger

logger = get_logger(__name__)


def _canonical_tick(
    quote: Mapping[str, Any],
    received_at: datetime,
) -> TickRecord:
    """Map one validated TCP quote into Data's canonical tick contract.

    Args:
        quote: Brokers-owned validated quote mapping.
        received_at: UTC time at which the gateway received the snapshot.

    Returns:
        Canonical provider-sourced latest-value tick.
    """
    return TickRecord(
        timestamp=datetime.fromtimestamp(
            cast("int", quote["time_msc"]) / 1_000, tz=UTC
        ),
        source="mt5",
        source_symbol=str(quote["symbol"]),
        source_revision="mt5-tcp-snapshot-v2",
        available_at=received_at,
        bid=cast("Decimal", quote["bid"]),
        ask=cast("Decimal", quote["ask"]),
        last=cast("Decimal | None", quote["last"]),
        volume=Decimal(cast("int", quote["volume"])),
        price_unit="quote_currency",
        volume_unit="ticks",
    )


async def iter_mt5_ticks(
    *,
    symbol: str,
    request_id: str,
) -> AsyncGenerator[TickRecord]:
    """Yield the latest quote for one symbol from each MT5 TCP snapshot.

    This stream intentionally represents one latest-value observation per
    second. It does not claim preservation of intermediate terminal ticks.

    Args:
        symbol: Exact broker-native symbol configured in the bridge EA.
        request_id: Canonical request identifier used for logging context.

    Yields:
        Canonical one-second MT5 quote observations.

    Raises:
        DataError: If the EA cannot apply the requested symbol.
    """
    from app.services.brokers import (
        acquire_metatrader_snapshot_symbols,
        release_metatrader_snapshot_symbols,
        stream_metatrader_snapshots,
    )

    logger.info("Opening MT5 TCP snapshot stream for %s (%s)", symbol, request_id)
    try:
        consumer_id = await acquire_metatrader_snapshot_symbols((symbol,))
    except (TimeoutError, ValueError) as error:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "mt5_symbol_demand"},
            request_id=request_id,
        ) from error
    try:
        async for snapshot in stream_metatrader_snapshots():
            received_at = cast("datetime", snapshot["received_at"])
            quotes = cast("tuple[Mapping[str, Any], ...]", snapshot["quotes"])
            for quote in quotes:
                if quote["symbol"] == symbol:
                    yield _canonical_tick(quote, received_at)
                    break
    finally:
        await release_metatrader_snapshot_symbols(consumer_id)


__all__: list[str] = []
