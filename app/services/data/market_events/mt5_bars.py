"""Retired MT5 live-bar polling boundary.

Live MT5 delivery is exclusively the MQL5 TCP latest-value snapshot channel.
Historical and bootstrap bars remain ordinary bounded broker reads; constructing
OHLCV bars from one-second observations would falsely imply tick completeness.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from app.services.data.contracts import DataError, OHLCVRecord


def iter_mt5_closed_bars(
    *,
    symbol: str,
    timeframe: str,
    request_id: str,
) -> AsyncGenerator[OHLCVRecord]:
    """Reject the retired Python-polled live-bar stream.

    Args:
        symbol: Exact broker-native symbol.
        timeframe: Requested chart timeframe.
        request_id: Canonical request identity.

    Returns:
        Async generator that raises ``UNSUPPORTED_OPERATION`` on iteration.
    """

    async def _unsupported() -> AsyncGenerator[OHLCVRecord]:
        """Raise from iteration so resource semantics remain generator-shaped.

        Yields:
            No records for valid requests.

        Raises:
            DataError: Always for a valid request identity.
        """
        if request_id:
            raise DataError(
                "UNSUPPORTED_OPERATION",
                safe_details={
                    "operation": "mt5_live_bar_stream",
                    "replacement": "mt5_tcp_snapshot_stream",
                    "symbol": symbol,
                    "timeframe": timeframe,
                },
                request_id=request_id,
            )
        yield OHLCVRecord.model_validate({})

    return _unsupported()


__all__: list[str] = []
